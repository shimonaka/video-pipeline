/**
 * 背景表示コンポーネント
 */

import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';

interface BackgroundProps {
    // 背景タイプ: 色指定 または 画像パス
    background: string;
}

// 組み込みの背景色プリセット
const COLOR_PRESETS: Record<string, string> = {
    lightBlue: '#e3f2fd',
    lightGreen: '#e8f5e9',
    lightPink: '#fce4ec',
    lightYellow: '#fffde7',
    lightGray: '#f5f5f5',
    white: '#ffffff',
    dark: '#1a1a2e',
    darkBlue: '#16213e',
};

export const Background: React.FC<BackgroundProps> = ({ background }) => {
    // プリセット色の場合
    if (COLOR_PRESETS[background]) {
        return (
            <AbsoluteFill style={{ backgroundColor: COLOR_PRESETS[background] }} />
        );
    }

    // CSS色コード（#xxx や rgb() など）の場合
    if (background.startsWith('#') || background.startsWith('rgb')) {
        return <AbsoluteFill style={{ backgroundColor: background }} />;
    }

    // 画像パスの場合
    return (
        <AbsoluteFill>
            <Img
                src={staticFile(background)}
                style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                }}
            />
        </AbsoluteFill>
    );
};
