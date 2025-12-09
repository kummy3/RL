#!/usr/bin/env python3
"""
Item 3 A2C 학습 스크립트 (A2C_3 버전)
- Neural Network: 128x2 layers
- Eval frequency: 10 episodes
- Multi-seed evaluation: 10 seeds
- WandB project: 1204_A2C_3_item3
"""

import os
import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

# 프로젝트 루트를 sys.path에 추가
PRJ_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PRJ_ROOT))

from config.paths import ITEMS_MAP, MASTER_JSON
from core.params_io import load_master_params
from core.data_manager import DataManager
from core.env_1113_revised_with_datamanager import GenerativeInvEnv, WeeklyInvEnv, CostParams

from stable_baselines3 import A2C
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor
import wandb
import json


# ========================================
# 콜백: 학습 진행상황 출력 및 WandB 로깅
# ========================================

class TrainingCallback(BaseCallback):
    """학습 중 에피소드 정보 로깅 (Step별 상세 로깅 포함)"""

    def __init__(self, print_freq=10000, output_dir=None, item=None, train_env=None, step_log_freq=10, verbose=0):
        super().__init__(verbose)
        self.print_freq = print_freq
        self.output_dir = output_dir
        self.item = item
        self.train_env = train_env
        self.step_log_freq = step_log_freq  # N step마다 로깅
        self.episode_rewards = []
        self.current_reward = 0
        self.current_length = 0
        self.episode_count = 0

        # 베스트 train 궤적 추적
        self.best_episode_reward = -np.inf
        self.current_trajectory = []

    def _on_step(self):
        reward = self.locals['rewards'][0]
        self.current_reward += reward
        self.current_length += 1

        # 현재 에피소드 궤적 기록
        info = self.locals.get('infos', [{}])[0]
        obs = self.locals['obs_tensor'].cpu().numpy()[0] if hasattr(self.locals.get('obs_tensor', None), 'cpu') else self.locals.get('new_obs', [[]])[0]
        action = self.locals['actions'][0]

        step_data = {
            'episode': self.episode_count + 1,
            't': self.current_length - 1,
            'action_idx': int(action),
            'reward': reward,
        }
        step_data.update(info)
        self.current_trajectory.append(step_data)

        # Step별 상세 로깅 (N step마다)
        if self.num_timesteps % self.step_log_freq == 0:
            wandb.log({
                "Train/Step/OrderQty": info.get('order_qty', 0),
                "Train/Step/OnHand": info.get('on_hand', 0),
                "Train/Step/Backlog": info.get('backlog', 0),
                "Train/Step/Reward": reward,
                "Train/Step/Demand": info.get('demand', 0),
                "Train/Step/HoldingCost": info.get('holding_cost', 0),
                "Train/Step/BacklogCost": info.get('backlog_cost', 0),
                "Train/Step/OrderCost": info.get('order_cost', 0),
                "Train/Step/TotalCost": info.get('cost', 0),
            }, step=self.num_timesteps)

        if self.locals['dones'][0]:
            self.episode_count += 1
            self.episode_rewards.append(self.current_reward)

            # Episode 평균 메트릭 계산
            traj_df = pd.DataFrame(self.current_trajectory)

            avg_onhand = traj_df['on_hand'].mean() if 'on_hand' in traj_df.columns else 0
            avg_orderqty = traj_df['order_qty'].mean() if 'order_qty' in traj_df.columns else 0
            avg_backlog = traj_df['backlog'].mean() if 'backlog' in traj_df.columns else 0

            # Action entropy 계산 (episode 동안의 action distribution)
            action_entropy = 0.0
            if 'action_idx' in traj_df.columns and len(traj_df) > 0:
                action_counts = traj_df['action_idx'].value_counts()
                action_probs = action_counts / len(traj_df)
                # H = -Σ p(a) * log(p(a))
                action_entropy = -np.sum(action_probs * np.log(action_probs + 1e-10))

            # WandB 에피소드 로깅
            wandb.log({
                "Episode": self.episode_count,
                "Train/EpisodeReturn": self.current_reward,
                "Train/EpisodeLength": self.current_length,
                "Train/Episode/Avg_OnHand": avg_onhand,
                "Train/Episode/Avg_OrderQty": avg_orderqty,
                "Train/Episode/Avg_Backlog": avg_backlog,
                "Train/Episode/ActionEntropy": action_entropy,
            }, step=self.num_timesteps)

            # 1. 에피소드별 jsonl 저장
            if self.output_dir is not None:
                jsonl_path = self.output_dir / f"item{self.item}_train_rewards.jsonl"
                with open(jsonl_path, 'a') as f:
                    json.dump({
                        "episode": int(self.episode_count),
                        "reward": float(self.current_reward),
                        "timesteps": int(self.current_length)
                    }, f)
                    f.write('\n')

            # 2. 베스트 train 궤적 갱신
            if self.current_reward > self.best_episode_reward:
                self.best_episode_reward = self.current_reward
                if self.output_dir is not None:
                    traj_df = pd.DataFrame(self.current_trajectory)
                    traj_path = self.output_dir / f"item{self.item}_best_train_trajectory.csv"
                    traj_df.to_csv(traj_path, index=False)
                    print(f"    -> [갱신] 새로운 베스트 (Train) 보상: {self.best_episode_reward:.3f}")

            self.current_reward = 0
            self.current_length = 0
            self.current_trajectory = []

        # 주기적 출력
        if self.num_timesteps % self.print_freq == 0 and len(self.episode_rewards) > 0:
            recent = self.episode_rewards[-10:]
            mean_r = np.mean(recent)
            std_r = np.std(recent)
            print(f"Steps: {self.num_timesteps:,} | Episodes: {self.episode_count} | "
                  f"Last 10 ep: {mean_r:.2f} ± {std_r:.2f}")

        return True


class BestModelCallback(BaseCallback):
    """
    Validation 성능이 개선될 때마다 모델을 저장하는 콜백
    """
    def __init__(self, eval_env, output_dir, eval_freq_steps, verbose=1):
        super().__init__(verbose)
        self.eval_env = eval_env
        self.output_dir = output_dir
        self.eval_freq_steps = eval_freq_steps
        self.best_val_reward = -np.inf
        self.eval_count = 0

    def _on_step(self):
        # eval_freq마다 평가 수행
        if self.num_timesteps % self.eval_freq_steps == 0 and self.num_timesteps > 0:
            self.eval_count += 1

            # Validation 평가 (평균 메트릭 포함)
            val_reward, val_metrics = self._evaluate(self.eval_env, n_episodes=1)

            # WandB 로깅
            wandb.log({
                "Eval/ValidationReward": val_reward,
                "Eval/Count": self.eval_count,
                "Eval/Avg_OnHand": val_metrics['avg_onhand'],
                "Eval/Avg_OrderQty": val_metrics['avg_orderqty'],
                "Eval/Avg_Backlog": val_metrics['avg_backlog'],
                "Eval/ActionEntropy": val_metrics['action_entropy'],
            }, step=self.num_timesteps)

            # 개선된 경우 모델 저장
            if val_reward > self.best_val_reward:
                self.best_val_reward = val_reward
                model_path = self.output_dir / "best_model_val.zip"
                self.model.save(model_path)
                if self.verbose > 0:
                    print(f"\n[Best Model] Validation 성능 개선! {val_reward:.4f} -> 모델 저장: {model_path}")

                # WandB에 최고 성능 기록
                wandb.log({
                    "Eval/BestValidationReward": self.best_val_reward,
                }, step=self.num_timesteps)

        return True

    def _evaluate(self, env, n_episodes=1):
        """환경에서 모델 평가 및 평균 메트릭 계산"""
        total_reward = 0.0
        all_trajectories = []

        for _ in range(n_episodes):
            obs, _ = env.reset()
            done = False
            episode_traj = []

            while not done:
                action, _ = self.model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(int(action))
                done = terminated or truncated
                total_reward += reward

                # Trajectory 기록
                step_data = {
                    'action_idx': int(action),
                    'on_hand': info.get('on_hand', 0),
                    'order_qty': info.get('order_qty', 0),
                    'backlog': info.get('backlog', 0),
                }
                episode_traj.append(step_data)

            all_trajectories.extend(episode_traj)

        # 평균 메트릭 계산
        traj_df = pd.DataFrame(all_trajectories)
        metrics = {
            'avg_onhand': traj_df['on_hand'].mean() if len(traj_df) > 0 else 0,
            'avg_orderqty': traj_df['order_qty'].mean() if len(traj_df) > 0 else 0,
            'avg_backlog': traj_df['backlog'].mean() if len(traj_df) > 0 else 0,
            'action_entropy': 0.0
        }

        # Action entropy 계산
        if len(traj_df) > 0 and 'action_idx' in traj_df.columns:
            action_counts = traj_df['action_idx'].value_counts()
            action_probs = action_counts / len(traj_df)
            metrics['action_entropy'] = -np.sum(action_probs * np.log(action_probs + 1e-10))

        return total_reward / n_episodes, metrics


# ========================================
# 평가 함수
# ========================================

def evaluate_policy(env, model, episodes=1, seed=123, deterministic=True):
    """모델 평가 및 trajectory 반환"""
    traj = []
    total_reward = 0.0

    for ep in range(episodes):
        obs, _ = env.reset(seed=seed + ep)
        done = False

        while not done:
            action, _ = model.predict(obs, deterministic=deterministic)
            obs, reward, terminated, truncated, info = env.step(int(action))
            done = terminated or truncated
            total_reward += reward

            row = {
                'episode': ep,
                'reward': reward,
                'action_idx': int(action),
            }
            row.update(info)
            traj.append(row)

    avg_reward = total_reward / episodes

    # 평균 메트릭 계산
    traj_df = pd.DataFrame(traj)
    metrics = {
        'avg_onhand': traj_df['on_hand'].mean() if 'on_hand' in traj_df.columns else 0,
        'avg_orderqty': traj_df['order_qty'].mean() if 'order_qty' in traj_df.columns else 0,
        'avg_backlog': traj_df['backlog'].mean() if 'backlog' in traj_df.columns else 0,
        'action_entropy': 0.0
    }

    # Action entropy 계산
    if len(traj_df) > 0 and 'action_idx' in traj_df.columns:
        action_counts = traj_df['action_idx'].value_counts()
        action_probs = action_counts / len(traj_df)
        metrics['action_entropy'] = -np.sum(action_probs * np.log(action_probs + 1e-10))

    return avg_reward, traj_df, metrics


def multi_seed_evaluation(dm, args, cost, final_model, output_dir, n_seeds=10):
    """다중 시드로 Test 평가 수행"""
    print("\n=== 다중 시드 Test 평가 (10 seeds) ===")

    test_seeds = [42, 123, 456, 789, 1000, 1111, 2222, 3333, 4444, 5555]
    test_rewards = []

    for i, seed in enumerate(test_seeds):
        # Test 환경 생성 (demand: historical test data, leadtime: test sampler)
        test_env = WeeklyInvEnv(
            data_manager=dm,
            item=args.item,
            mode='test',
            history_length=args.history_length,
            cost=cost,
            action_unit=args.action_unit,
            max_order=args.max_order,
            seed=seed,  # 다른 시드로 리드타임 샘플링
            pipeline_horizon=args.pipeline_horizon,
            reward_scale=args.reward_scale,
        )

        reward, traj, metrics = evaluate_policy(test_env, final_model, episodes=1, seed=seed)
        test_rewards.append(reward)

        # 궤적 저장
        traj_path = output_dir / f"test_trajectory_seed{seed}.csv"
        traj.to_csv(traj_path, index=False)

        print(f"  시드 {seed:4d} (#{i+1:2d}/10): Test Reward = {reward:.4f}, "
              f"Avg OnHand = {metrics['avg_onhand']:.2f}, Entropy = {metrics['action_entropy']:.4f}")

    # 통계 계산
    test_mean = np.mean(test_rewards)
    test_std = np.std(test_rewards)
    test_ci95 = 1.96 * test_std / np.sqrt(len(test_seeds))

    print(f"\n다중 시드 평가 결과:")
    print(f"  Test 평균: {test_mean:.4f}")
    print(f"  Test 표준편차: {test_std:.4f}")
    print(f"  Test 95% 신뢰구간: ±{test_ci95:.4f}")
    print(f"  Test 범위: [{min(test_rewards):.4f}, {max(test_rewards):.4f}]")

    # WandB 로깅
    wandb.log({
        "Final/Test_MultiSeed_Mean": test_mean,
        "Final/Test_MultiSeed_Std": test_std,
        "Final/Test_MultiSeed_CI95": test_ci95,
        "Final/Test_MultiSeed_Min": min(test_rewards),
        "Final/Test_MultiSeed_Max": max(test_rewards),
    })

    # 개별 시드 결과도 로깅
    for i, (seed, reward) in enumerate(zip(test_seeds, test_rewards)):
        wandb.log({f"Final/Test_Seed{seed}": reward})

    return test_mean, test_std, test_ci95, test_rewards


# ========================================
# 메인 실행
# ========================================

def main():
    parser = argparse.ArgumentParser(description="A2C Item3 Training (A2C_3)")
    parser.add_argument("--item", type=int, default=3, help="Item number")
    parser.add_argument("--episodes", type=int, default=20000, help="Number of episodes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--n_steps", type=int, default=342, help="N steps for A2C")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--gae_lambda", type=float, default=0.95, help="GAE lambda")
    parser.add_argument("--ent_coef", type=float, default=0.01, help="Entropy coefficient")
    parser.add_argument("--vf_coef", type=float, default=0.5, help="Value function coefficient")
    parser.add_argument("--eval_freq", type=int, default=10, help="Eval frequency (episodes)")
    parser.add_argument("--output_dir", type=str, default="outputs/a2c_item3", help="Output directory")

    # Cost parameters
    parser.add_argument("--cost_h", type=float, default=0.10, help="Holding cost")
    parser.add_argument("--cost_b", type=float, default=0.10, help="Backlog cost")
    parser.add_argument("--cost_c", type=float, default=0.10, help="Order cost per unit")
    parser.add_argument("--cost_K", type=float, default=0.00, help="Fixed order cost")
    parser.add_argument("--cost_N", type=float, default=0.0789, help="Nors 계수(KF-16)")

    # Environment parameters
    parser.add_argument("--action_unit", type=int, default=1, help="Action unit")
    parser.add_argument("--max_order", type=int, default=190, help="Max order quantity")
    parser.add_argument("--history_length", type=int, default=12, help="History length (k_past)")
    parser.add_argument("--pipeline_horizon", type=int, default=31, help="Pipeline horizon")
    parser.add_argument("--reward_scale", type=float, default=1.0, help="Reward scaling factor (1.0 = no scaling)")

    args = parser.parse_args()

    # WandB 초기화 (키 파일에서 읽기)
    wandb_key_path = Path.home().parent / "kumhee" / ".wandb_key"
    if wandb_key_path.exists():
        with open(wandb_key_path, 'r') as f:
            wandb_key = f.read().strip()
        wandb.login(key=wandb_key)
        print(f"WandB 로그인 완료 (키 파일: {wandb_key_path})")
    else:
        print(f"경고: WandB 키 파일 없음 ({wandb_key_path})")
        wandb.login()  # 환경 변수 또는 기존 로그인 사용

    # Sweep 실행 시에는 project 지정하지 않음 (YAML에서 정의)
    # 일반 실행 시에는 project 지정
    wandb_config = {
        "config": vars(args),
        "sync_tensorboard": False,
    }

    # wandb.run이 None이면 일반 실행, 있으면 sweep 실행
    if os.environ.get("WANDB_SWEEP_ID") is None:
        wandb_config["project"] = "1204_A2C_3_item3"
        wandb_config["name"] = f"a2c_item3_exp3_solo"

    run = wandb.init(**wandb_config)

    # Sweep 실행 시 run name 커스터마이징
    if os.environ.get("WANDB_SWEEP_ID") is not None:
        lr = wandb.config.get("lr", 0)
        ent_coef = wandb.config.get("ent_coef", 0)
        n_steps = wandb.config.get("n_steps", 0)
        run_name = f"item{args.item}_{lr}_{ent_coef}_{n_steps}"
        wandb.run.name = run_name
        wandb.run.save()

    # 출력 디렉토리 생성 (WandB run ID 포함)
    base_output_dir = Path(args.output_dir)
    output_dir = base_output_dir / f"run_{wandb.run.id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 설정 출력
    print(f"\n{'='*60}")
    print(f"A2C Training for Item {args.item} (A2C_3)")
    print(f"{'='*60}")
    print(f"Episodes: {args.episodes}")
    print(f"Learning rate: {args.lr}")
    print(f"N steps: {args.n_steps}")
    print(f"Gamma: {args.gamma}")
    print(f"GAE lambda: {args.gae_lambda}")
    print(f"Entropy coef: {args.ent_coef}")
    print(f"Eval frequency: {args.eval_freq} episodes")
    print(f"Neural Network: [128, 128] (2 layers)")
    print(f"{'='*60}\n")

    # Cost 파라미터
    cost = CostParams(
        h=args.cost_h,
        b=args.cost_b,
        c=args.cost_c,
        K=args.cost_K,
        N=args.cost_N
    )

    try:
        # ========================================
        # 1. 데이터 준비
        # ========================================
        print("=== 데이터 준비 ===")
        best_params = load_master_params(MASTER_JSON)
        dm = DataManager(ITEMS_MAP, best_params, rng_seed=args.seed)
        buf = dm.prepare_item(args.item)

        # Episode 길이 = train 데이터 길이
        episode_len = len(buf["demand_arrays"]["train"])
        print(f"Train 데이터 길이: {episode_len} weeks")
        print(f"Valid 데이터 길이: {len(buf['demand_arrays']['valid'])} weeks")
        print(f"Test 데이터 길이: {len(buf['demand_arrays']['test'])} weeks")
        print("완료!\n")

        # ========================================
        # 2. 환경 생성
        # ========================================
        print("=== 환경 생성 ===")

        # Train 환경 (GenerativeInvEnv - 샘플링 사용)
        train_env = GenerativeInvEnv(
            data_manager=dm,
            item=args.item,
            mode='train',
            episode_len=episode_len,
            cost=cost,
            action_unit=args.action_unit,
            max_order=args.max_order,
            initial_on_hand=0.0,
            allow_backlog=True,
            history_length=args.history_length,
            seed=args.seed,
            pipeline_horizon=args.pipeline_horizon,
            reward_scale=args.reward_scale,
        )

        # Valid 환경 (WeeklyInvEnv - 실제 데이터 사용)
        valid_env = WeeklyInvEnv(
            data_manager=dm,
            item=args.item,
            mode='valid',
            history_length=args.history_length,
            cost=cost,
            action_unit=args.action_unit,
            max_order=args.max_order,
            seed=args.seed + 1000,
            pipeline_horizon=args.pipeline_horizon,
            reward_scale=args.reward_scale,
        )
        valid_env = Monitor(valid_env)

        # Test 환경 (최종 평가용)
        test_env = WeeklyInvEnv(
            data_manager=dm,
            item=args.item,
            mode='test',
            history_length=args.history_length,
            cost=cost,
            action_unit=args.action_unit,
            max_order=args.max_order,
            seed=args.seed + 2000,
            pipeline_horizon=args.pipeline_horizon,
            reward_scale=args.reward_scale,
        )

        print(f"Observation dim: {train_env.observation_space.shape[0]}")
        print(f"Action space: {train_env.action_space.n} actions")
        print(f"Scale factors (train): d={train_env.scale_d:.2f}, onhand={train_env.scale_onhand:.2f}, "
              f"backlog={train_env.scale_backlog:.2f}, pending={train_env.scale_pending:.2f}")
        print("완료!\n")

        # ========================================
        # 3. A2C 모델 생성 (Neural Network: 128x2)
        # ========================================
        print("=== A2C 모델 초기화 (Neural Network: [128, 128]) ===")

        total_timesteps = args.episodes * episode_len
        eval_freq_steps = args.eval_freq * episode_len

        # Policy network architecture: 128x2 layers
        policy_kwargs = dict(
            net_arch=dict(pi=[256, 256], vf=[256, 256])  # Actor와 Critic 모두 256x2 (A2C_4)
        )

        model = A2C(
            "MlpPolicy",
            train_env,
            learning_rate=args.lr,
            n_steps=args.n_steps,
            gamma=args.gamma,
            gae_lambda=args.gae_lambda,
            ent_coef=args.ent_coef,
            vf_coef=args.vf_coef,
            max_grad_norm=0.5,
            policy_kwargs=policy_kwargs,  # 256x2 network (A2C_4)
            verbose=0,
            seed=args.seed,
            device='auto',  # Auto-detect GPU
        )

        print(f"Total timesteps: {total_timesteps:,}")
        print(f"Eval frequency: {eval_freq_steps:,} steps ({args.eval_freq} episodes)")
        print("완료!\n")

        # ========================================
        # 4. 콜백 설정
        # ========================================
        training_callback = TrainingCallback(
            print_freq=episode_len * 10,
            output_dir=output_dir,
            item=args.item,
            train_env=train_env,
            step_log_freq=10  # 10 step마다 상세 로깅
        )

        # Best model 저장 콜백 (validation 성능 기반)
        best_model_callback = BestModelCallback(
            eval_env=valid_env,
            output_dir=output_dir,
            eval_freq_steps=eval_freq_steps,
            verbose=1
        )

        # 주기적 체크포인트 (500 에피소드마다)
        checkpoint_callback = CheckpointCallback(
            save_freq=500 * episode_len,
            save_path=str(output_dir / "checkpoints"),
            name_prefix="a2c_model",
            save_replay_buffer=False,
            save_vecnormalize=False,
        )

        # ========================================
        # 5. 학습
        # ========================================
        print("=== A2C 학습 시작 ===")
        model.learn(
            total_timesteps=total_timesteps,
            callback=[training_callback, best_model_callback, checkpoint_callback],
            progress_bar=True,
        )
        print("=== 학습 완료 ===\n")

        # ========================================
        # 6. Best 모델 로드 및 평가
        # ========================================
        best_model_path = output_dir / "best_model_val.zip"
        if best_model_path.exists():
            print(f"Best 모델 로드: {best_model_path}")
            final_model = A2C.load(best_model_path, device="auto")
        else:
            print("Best 모델 없음, 현재 모델 사용")
            final_model = model

        # Train 평가
        print("\n=== Train 평가 ===")
        train_eval_env = WeeklyInvEnv(
            data_manager=dm,
            item=args.item,
            mode='train',
            history_length=args.history_length,
            cost=cost,
            action_unit=args.action_unit,
            max_order=args.max_order,
            seed=args.seed + 3000,
            pipeline_horizon=args.pipeline_horizon,
            reward_scale=args.reward_scale,
        )
        train_reward, train_traj, train_metrics = evaluate_policy(train_eval_env, final_model, episodes=1)
        print(f"Train reward: {train_reward:.4f}")
        print(f"Train trajectory length: {len(train_traj)} steps")
        print(f"Train metrics: OnHand={train_metrics['avg_onhand']:.2f}, "
              f"OrderQty={train_metrics['avg_orderqty']:.2f}, Entropy={train_metrics['action_entropy']:.4f}")

        # Valid 평가
        print("\n=== Valid 평가 ===")
        valid_eval_env = WeeklyInvEnv(
            data_manager=dm,
            item=args.item,
            mode='valid',
            history_length=args.history_length,
            cost=cost,
            action_unit=args.action_unit,
            max_order=args.max_order,
            seed=args.seed + 4000,
            pipeline_horizon=args.pipeline_horizon,
            reward_scale=args.reward_scale,
        )
        valid_reward, valid_traj, valid_metrics = evaluate_policy(valid_eval_env, final_model, episodes=1)
        print(f"Valid reward: {valid_reward:.4f}")
        print(f"Valid trajectory length: {len(valid_traj)} steps")
        print(f"Valid metrics: OnHand={valid_metrics['avg_onhand']:.2f}, "
              f"OrderQty={valid_metrics['avg_orderqty']:.2f}, Entropy={valid_metrics['action_entropy']:.4f}")

        # Test 평가 (단일 시드)
        print("\n=== Test 평가 (단일 시드) ===")
        test_reward, test_traj, test_metrics = evaluate_policy(test_env, final_model, episodes=1)
        print(f"Test reward: {test_reward:.4f}")
        print(f"Test trajectory length: {len(test_traj)} steps")
        print(f"Test metrics: OnHand={test_metrics['avg_onhand']:.2f}, "
              f"OrderQty={test_metrics['avg_orderqty']:.2f}, Entropy={test_metrics['action_entropy']:.4f}")

        # WandB 로깅
        wandb.log({
            "Final/TrainReward": train_reward,
            "Final/ValidReward": valid_reward,
            "Final/TestReward": test_reward,
            "Final/Train_Avg_OnHand": train_metrics['avg_onhand'],
            "Final/Train_Avg_OrderQty": train_metrics['avg_orderqty'],
            "Final/Train_ActionEntropy": train_metrics['action_entropy'],
            "Final/Valid_Avg_OnHand": valid_metrics['avg_onhand'],
            "Final/Valid_Avg_OrderQty": valid_metrics['avg_orderqty'],
            "Final/Valid_ActionEntropy": valid_metrics['action_entropy'],
            "Final/Test_Avg_OnHand": test_metrics['avg_onhand'],
            "Final/Test_Avg_OrderQty": test_metrics['avg_orderqty'],
            "Final/Test_ActionEntropy": test_metrics['action_entropy'],
        })

        # ========================================
        # 7. 다중 시드 Test 평가 (10 seeds)
        # ========================================
        test_mean, test_std, test_ci95, test_rewards = multi_seed_evaluation(
            dm, args, cost, final_model, output_dir, n_seeds=10
        )

        # ========================================
        # 8. 결과 저장
        # ========================================
        print("\n=== 결과 저장 ===")

        train_traj.to_csv(output_dir / "train_trajectory.csv", index=False)
        valid_traj.to_csv(output_dir / "valid_trajectory.csv", index=False)
        test_traj.to_csv(output_dir / "test_trajectory.csv", index=False)
        model.save(output_dir / "final_model.zip")

        # 다중 시드 결과 저장
        multi_seed_results = pd.DataFrame({
            'seed': [42, 123, 456, 789, 1000, 1111, 2222, 3333, 4444, 5555],
            'test_reward': test_rewards
        })
        multi_seed_results.to_csv(output_dir / "test_multi_seed_results.csv", index=False)

        print(f"Train trajectory: {output_dir / 'train_trajectory.csv'}")
        print(f"Valid trajectory: {output_dir / 'valid_trajectory.csv'}")
        print(f"Test trajectory: {output_dir / 'test_trajectory.csv'}")
        print(f"Multi-seed results: {output_dir / 'test_multi_seed_results.csv'}")
        print(f"Final model: {output_dir / 'final_model.zip'}")

        # ========================================
        # 9. 최종 요약
        # ========================================
        print(f"\n{'='*60}")
        print("=== 최종 결과 요약 ===")
        print(f"{'='*60}")
        print(f"Item: {args.item}")
        print(f"Episodes: {args.episodes}")
        print(f"Neural Network: [128, 128]")
        print(f"Eval Frequency: {args.eval_freq} episodes")
        print(f"---")
        print(f"Train reward: {train_reward:.4f}")
        print(f"Valid reward: {valid_reward:.4f}")
        print(f"Test reward (single seed): {test_reward:.4f}")
        print(f"Test reward (multi-seed avg): {test_mean:.4f} ± {test_ci95:.4f}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n!!! Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        wandb.finish()


if __name__ == "__main__":
    main()
