/**
 * Rhubarb Lip Sync の出力型定義
 */

// Rhubarbが出力する口形状（9種類）
export type RhubarbShape = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'X';

// アセットで用意する口形状（6種類に正規化）
export type MouthShape = 'A' | 'B' | 'C' | 'D' | 'E' | 'F';

// Rhubarbの口形状キュー
export interface MouthCue {
  start: number;  // 開始時間（秒）
  end: number;    // 終了時間（秒）
  value: RhubarbShape;
}

// Rhubarbの出力JSONフォーマット
export interface RhubarbOutput {
  metadata: {
    soundFile: string;
    duration: number;
  };
  mouthCues: MouthCue[];
}

// 口形状の正規化マッピング（9→6）
export const SHAPE_FALLBACK: Record<RhubarbShape, MouthShape> = {
  A: 'A',  // 閉じた口（休止）
  B: 'B',  // 少し開いた口（m, b, p）
  C: 'C',  // 開いた口（e, a等の母音）
  D: 'D',  // 広く開いた口（a, o）
  E: 'E',  // 横に引いた口（i, e）
  F: 'F',  // 突き出した口（u, o, w）
  G: 'B',  // f, v → Bにフォールバック
  H: 'C',  // l → Cにフォールバック
  X: 'A',  // 無音/不明 → Aにフォールバック
};

// フレーム番号から口形状を取得
export function getMouthShapeAtFrame(
  mouthCues: MouthCue[],
  frame: number,
  fps: number
): MouthShape {
  const time = frame / fps;
  
  for (const cue of mouthCues) {
    if (time >= cue.start && time < cue.end) {
      return SHAPE_FALLBACK[cue.value];
    }
  }
  
  // デフォルトは閉じた口
  return 'A';
}
