/**
 * Remotion Root - Composition定義
 */

import { Composition } from 'remotion';
import { MultiSceneVideo } from './MultiSceneVideo';

export const RemotionRoot: React.FC = () => {
    return (
        <>
            {/* メインの動画Composition */}
            <Composition
                id="MultiSceneVideo"
                component={MultiSceneVideo}
                durationInFrames={300}  // 実際はpipeline-dataで上書きされる
                fps={30}
                width={1920}
                height={1080}
                defaultProps={{
                    dataPath: 'pipeline-data.json',
                }}
                // 動的に長さを計算
                calculateMetadata={async () => {
                    try {
                        const res = await fetch('/public/pipeline-data.json');
                        if (res.ok) {
                            const data = await res.json();
                            return {
                                durationInFrames: data.totalFrames || 300,
                                fps: data.videoConfig?.fps || 30,
                                width: data.videoConfig?.width || 1920,
                                height: data.videoConfig?.height || 1080,
                            };
                        }
                    } catch (e) {
                        console.warn('メタデータ取得失敗、デフォルト値を使用:', e);
                    }
                    return {};
                }}
            />

            {/* テスト用: 固定長の単純なComposition */}
            <Composition
                id="TestVideo"
                component={() => (
                    <div
                        style={{
                            backgroundColor: '#e3f2fd',
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            fontSize: 64,
                            fontFamily: 'sans-serif',
                        }}
                    >
                        テスト動画
                    </div>
                )}
                durationInFrames={90}
                fps={30}
                width={1920}
                height={1080}
            />
        </>
    );
};
