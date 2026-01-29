/**
 * 字幕表示コンポーネント (YouTube風デザイン)
 */

import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

interface SubtitleDisplayProps {
    text: string;
    speaker?: string; // 演者ID
    // スタイル
    fontSize?: number;
    fontFamily?: string;
    // 位置
    bottom?: number;
    // フェードアニメーション
    fadeInDuration?: number;
    fadeOutDuration?: number;
    totalDuration?: number;
    frameOffset?: number;
}

// 演者別カラー定義
const SPEAKER_COLORS: Record<string, string> = {
    // 3: ずんだもん (緑)
    "3": "#3EA150",
    "zundamon": "#3EA150",
    // 2: 四国めたん (ピンク)
    "2": "#A93064",
    "metan": "#A93064",
    // 8: 春日部つむぎ (黄色/黄緑)
    "8": "#EAD943",
    "tsumugi": "#EAD943",
    // 47: ナースロボ (白/赤) -> 今回はないけど例
    // ナレーター (黒)
    "narrator": "#000000",
    // デフォルト (青)
    "default": "#1E90FF"
};

// 強調キーワード色
const HIGHLIGHT_COLOR = "#FFD700";

export const SubtitleDisplay: React.FC<SubtitleDisplayProps> = ({
    text,
    speaker = "narrator",
    fontSize = 64, // 大きく
    fontFamily = '"Noto Sans JP", sans-serif',
    bottom = 80,
    fadeInDuration = 5, // ポップにするため短く
    fadeOutDuration = 5,
    totalDuration = 100,
    frameOffset = 0,
}) => {
    const frame = useCurrentFrame();
    const relativeFrame = frame - frameOffset;

    // フェードイン/アウトのアニメーション
    const opacity = interpolate(
        relativeFrame,
        [0, fadeInDuration, totalDuration - fadeOutDuration, totalDuration],
        [0, 1, 1, 0],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    if (!text) return null;

    // 演者カラー決定
    const mainColor = SPEAKER_COLORS[speaker] || SPEAKER_COLORS["default"];

    // テキスト解析（*強調*）
    const parseText = (inputText: string) => {
        const parts = inputText.split(/\*(.*?)\*/g);
        return parts.map((part, index) => {
            // 奇数番目が強調部分
            const isHighlight = index % 2 === 1;
            return (
                <span
                    key={index}
                    style={{
                        color: isHighlight ? HIGHLIGHT_COLOR : 'inherit',
                    }}
                >
                    {part}
                </span>
            );
        });
    };

    const content = parseText(text);

    // 共通テキストスタイル
    const commonTextStyle: React.CSSProperties = {
        fontFamily,
        fontWeight: 900, // Black
        fontSize,
        whiteSpace: 'pre-wrap',
        textAlign: 'center',
        lineHeight: 1.4,
    };

    return (
        <div
            style={{
                position: 'absolute',
                bottom,
                left: '50%',
                transform: 'translateX(-50%)',
                opacity,
                width: '90%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'flex-end',
            }}
        >
            <div style={{ position: 'relative' }}>
                {/* Layer 3: 外側の白フチ (4px + 10px = 14px くらいのはみ出しが必要だが、strokeは中心からなので倍) */}
                {/* 縁取り②: 白 4px (色の外側) -> 文字+10px+4px = 14px stroke on top of color? */}
                {/* 計算: Main(0) -> ColorBorder(10px) -> WhiteBorder(4px) */}
                {/* WebkitTextStrokeは太さ。ColorBorderを20px(片側10px)、WhiteBorderを28px(片側14px)とする */}

                {/* 最背面: 白フチ (一番太い) */}
                <div
                    style={{
                        ...commonTextStyle,
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        color: 'white',
                        WebkitTextStroke: '28px white', // 片側14px
                        zIndex: 0,
                    }}
                >
                    {content}
                </div>

                {/* 文字配列ズレ防止のためのダミー (高さ確保) */}
                {/* absoluteだと高さが潰れるので、Relatveな要素が必要だが、strokeの影響を受けないようにする */}

                {/* 中間: 色フチ */}
                <div
                    style={{
                        ...commonTextStyle,
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        color: mainColor,
                        WebkitTextStroke: '20px ' + mainColor, // 片側10px
                        zIndex: 1,
                    }}
                >
                    {content}
                </div>

                {/* 最前面: メイン白文字 */}
                <div
                    style={{
                        ...commonTextStyle,
                        position: 'relative', // これが基準
                        color: 'white',
                        zIndex: 2,
                    }}
                >
                    {content}
                </div>
            </div>
        </div>
    );
};
