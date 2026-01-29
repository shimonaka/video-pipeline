/**
 * 動画パイプラインデータの型定義
 */

import { MouthCue } from './lipsync';

// シーンデータ
export interface SceneData {
    sceneId: string;
    speaker: string;
    text: string;
    audio: {
        file: string;
        duration: number;
        startFrame: number;
        endFrame: number;
    };
    lipsync: {
        file: string;
    };
    background?: string;
}

// 動画設定
export interface VideoConfig {
    width: number;
    height: number;
    fps: number;
    background: string;
    characterVisible?: boolean;
}

// パイプラインデータ（pipeline-data.json）
export interface PipelineData {
    title: string;
    version: string;
    videoConfig: VideoConfig;
    scenes: SceneData[];
    totalFrames: number;
}

// ロード済みのシーンデータ（リップシンク含む）
export interface LoadedScene extends SceneData {
    lipsyncData: {
        mouthCues: MouthCue[];
    };
}
