/**
 * 複数シーン対応の動画コンポーネント
 * pipeline-data.jsonを読み込んで動画を構成
 */

import React, { useEffect, useState } from 'react';
import {
    AbsoluteFill,
    Audio,
    Sequence,
    continueRender,
    delayRender,
    staticFile,
} from 'remotion';
import { Character, SubtitleDisplay, Background } from './components';
import { PipelineData, LoadedScene, MouthCue } from './types';

interface MultiSceneVideoProps {
    // データファイルパス（デフォルト: public/pipeline-data.json）
    dataPath?: string;
}

export const MultiSceneVideo: React.FC<MultiSceneVideoProps> = ({
    dataPath = 'pipeline-data.json',
}) => {
    const [handle] = useState(() => delayRender());
    const [pipelineData, setPipelineData] = useState<PipelineData | null>(null);
    const [loadedScenes, setLoadedScenes] = useState<LoadedScene[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                // パイプラインデータ読み込み
                const pipelineRes = await fetch(staticFile(dataPath));
                if (!pipelineRes.ok) {
                    throw new Error(`pipeline-data.json の読み込みに失敗: ${pipelineRes.status}`);
                }
                const data: PipelineData = await pipelineRes.json();
                setPipelineData(data);

                // 各シーンのリップシンクデータを読み込み
                const scenes: LoadedScene[] = await Promise.all(
                    data.scenes.map(async (scene) => {
                        try {
                            const lipsyncRes = await fetch(staticFile(scene.lipsync.file));
                            if (!lipsyncRes.ok) {
                                console.warn(`リップシンクファイル読み込み失敗: ${scene.lipsync.file}`);
                                return {
                                    ...scene,
                                    lipsyncData: { mouthCues: [] },
                                };
                            }
                            const lipsyncJson = await lipsyncRes.json();
                            return {
                                ...scene,
                                lipsyncData: {
                                    mouthCues: lipsyncJson.mouthCues as MouthCue[],
                                },
                            };
                        } catch (e) {
                            console.warn(`リップシンク読み込みエラー: ${scene.sceneId}`, e);
                            return {
                                ...scene,
                                lipsyncData: { mouthCues: [] },
                            };
                        }
                    })
                );

                setLoadedScenes(scenes);
                continueRender(handle);
            } catch (e) {
                console.error('データ読み込みエラー:', e);
                setError(e instanceof Error ? e.message : String(e));
                continueRender(handle);
            }
        };

        loadData();
    }, [dataPath, handle]);

    if (error) {
        return (
            <AbsoluteFill
                style={{
                    backgroundColor: '#1a1a2e',
                    justifyContent: 'center',
                    alignItems: 'center',
                }}
            >
                <div
                    style={{
                        color: '#ff6b6b',
                        fontSize: 32,
                        fontFamily: 'sans-serif',
                        textAlign: 'center',
                        padding: 40,
                    }}
                >
                    エラー: {error}
                </div>
            </AbsoluteFill>
        );
    }

    if (!pipelineData) {
        return (
            <AbsoluteFill
                style={{
                    backgroundColor: '#1a1a2e',
                    justifyContent: 'center',
                    alignItems: 'center',
                }}
            >
                <div style={{ color: '#ffffff', fontSize: 24, fontFamily: 'sans-serif' }}>
                    読み込み中...
                </div>
            </AbsoluteFill>
        );
    }

    const { videoConfig } = pipelineData;

    return (
        <AbsoluteFill>
            {/* 背景（全シーン共通またはシーン別） */}
            <Background background={videoConfig.background} />

            {/* 各シーンをSequenceで配置 */}
            {loadedScenes.map((scene, index) => {
                const sceneDuration = scene.audio.endFrame - scene.audio.startFrame;
                const startFrom = scene.audio.startFrame;

                return (
                    <Sequence
                        key={scene.sceneId}
                        from={startFrom}
                        durationInFrames={sceneDuration}
                        name={`Scene ${index + 1}: ${scene.speaker}`}
                    >
                        {/* シーン別背景（指定がある場合） */}
                        {scene.background && <Background background={scene.background} />}

                        {/* 音声 */}
                        <Audio src={staticFile(scene.audio.file)} />

                        {/* キャラクター（表示設定がある場合のみ） */}
                        {(videoConfig.characterVisible !== false) && (
                            <Character
                                mouthCues={scene.lipsyncData.mouthCues}
                                x={200}
                                y={100}
                                width={400}
                                height={500}
                                frameOffset={0}
                            />
                        )}

                        {/* 字幕 */}
                        <SubtitleDisplay
                            text={scene.text}
                            speaker={scene.speaker}
                            totalDuration={sceneDuration}
                            fadeInDuration={Math.min(10, sceneDuration / 4)}
                            fadeOutDuration={Math.min(10, sceneDuration / 4)}
                        />
                    </Sequence>
                );
            })}
        </AbsoluteFill>
    );
};
