/**
 * キャラクター表示コンポーネント（口パク対応）
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, Img, staticFile } from 'remotion';
import { MouthCue, MouthShape, getMouthShapeAtFrame } from '../types/lipsync';

interface CharacterProps {
    // キャラクター画像のベースパス（口なし）- undefinedの場合は口のみ表示
    basePath?: string;
    // 口形状画像のディレクトリ
    mouthDir?: string;
    // リップシンクデータ
    mouthCues?: MouthCue[];
    // 位置・サイズ
    x?: number;
    y?: number;
    width?: number;
    height?: number;
    // フレームオフセット（シーン開始フレーム）
    frameOffset?: number;
}

export const Character: React.FC<CharacterProps> = ({
    basePath,  // デフォルトをundefinedに変更
    mouthDir = 'character',
    mouthCues = [],
    x = 100,
    y = 200,
    width = 300,
    height = 400,
    frameOffset = 0,
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // 現在フレームでの口形状を取得
    const relativeFrame = frame - frameOffset;
    const mouthShape = getMouthShapeAtFrame(mouthCues, relativeFrame, fps);

    // 口画像のパス
    const mouthPath = `${mouthDir}/mouth-${mouthShape}.png`;

    return (
        <div
            style={{
                position: 'absolute',
                left: x,
                top: y,
                width,
                height,
            }}
        >
            {/* ベース画像（指定がある場合のみ） */}
            {basePath && (
                <Img
                    src={staticFile(basePath)}
                    style={{
                        position: 'absolute',
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain',
                    }}
                />
            )}
            {/* 口画像 */}
            <Img
                src={staticFile(mouthPath)}
                style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    objectPosition: 'bottom',
                }}
            />
        </div>
    );
};
