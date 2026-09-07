/**
 * PulseOS 极客工作台 - 酷狗音乐核心 API 模块 (kugouApi.ts)
 * 支持：扫码登录、轮询检测、个人歌单/我喜欢提取、音源解析、歌词同步
 */

export interface QRLoginSession {
  key: string;
  qrUrl: string;
  qrImg?: string;
}

export type QRStatus = 'waiting' | 'scanned' | 'success' | 'expired' | 'failed';

export interface UserProfile {
  userId: string;
  nickname: string;
  avatar: string;
  cookie: string;
  isVip?: boolean;
}

export interface QRLoginCheckResult {
  status: QRStatus;
  message: string;
  user?: UserProfile;
}

export interface KugouPlaylist {
  id: string;
  name: string;
  cover: string;
  count: number;
  isFavorite: boolean;
  description?: string;
}

export interface KugouSong {
  id: string; // Hash or song ID
  name: string;
  singer: string;
  album: string;
  duration: number; // 秒
  cover: string;
  quality: 'Standard' | 'HQ' | 'SQ' | 'Hi-Res';
  url?: string;
}

export interface LyricLine {
  time: number; // 秒数
  text: string;
}

const API_BASE = '/api/music/api/v1';
const USER_STORAGE_KEY = 'pulseos_kugou_user';

class KugouApiClient {
  private user: UserProfile | null = null;

  constructor() {
    this.loadUserFromStorage();
  }

  public loadUserFromStorage(): UserProfile | null {
    try {
      const saved = localStorage.getItem(USER_STORAGE_KEY);
      if (saved) {
        this.user = JSON.parse(saved);
        return this.user;
      }
    } catch (e) {
      console.warn('Failed to load user profile from storage', e);
    }
    this.user = null;
    return null;
  }

  public saveUserToStorage(user: UserProfile): void {
    this.user = user;
    try {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    } catch (e) {
      console.warn('Failed to save user profile to storage', e);
    }
  }

  public logout(): void {
    this.user = null;
    try {
      localStorage.removeItem(USER_STORAGE_KEY);
    } catch (e) {}
  }

  public getCurrentUser(): UserProfile | null {
    return this.user;
  }

  public isLoggedIn(): boolean {
    return !!(this.user && this.user.cookie);
  }

  /**
   * 1. 扫码登录：生成登录二维码会话
   */
  public async createQRLogin(): Promise<QRLoginSession> {
    const res = await fetch(`${API_BASE}/system/qr_login/kugou`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!res.ok) {
      throw new Error(`生成二维码失败: HTTP ${res.status}`);
    }

    const d = await res.json();
    const data = d.data || d;
    return {
      key: data.key || data.qr_key || '',
      qrUrl: data.qr_url || data.url || `https://login-user.kugou.com/v1/qrcode/jump?key=${data.key}`,
      qrImg: data.qr_img || data.img
    };
  }

  /**
   * 2. 扫码登录：轮询检查二维码状态
   */
  public async checkQRLogin(key: string): Promise<QRLoginCheckResult> {
    const res = await fetch(`${API_BASE}/system/qr_login/kugou?key=${encodeURIComponent(key)}`);
    if (!res.ok) {
      return { status: 'failed', message: `检测失败 (HTTP ${res.status})` };
    }

    const d = await res.json();
    const data = d.data || d;

    // 根据 go-music-api 或 kugou 状态码解析
    const rawStatus = (data.status || '').toLowerCase();
    const code = data.code || d.code;

    if (rawStatus === 'success' || code === 200 && data.cookie) {
      const user: UserProfile = {
        userId: data.userid || data.userId || 'kugou_user',
        nickname: data.nickname || data.username || '酷狗极客音乐家',
        avatar: data.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100',
        cookie: data.cookie || ''
      };
      this.saveUserToStorage(user);
      return { status: 'success', message: '登录成功', user };
    } else if (rawStatus === 'scanned' || rawStatus === 'confirm' || code === 201) {
      return { status: 'scanned', message: '已扫码，请在手机酷狗上点击确认登录' };
    } else if (rawStatus === 'expired' || code === 202) {
      return { status: 'expired', message: '二维码已过期，请重新刷新' };
    } else {
      return { status: 'waiting', message: '请使用酷狗音乐 App 扫码' };
    }
  }

  /**
   * 3. 获取用户个人歌单列表 (包含我喜欢和自建歌单)
   */
  public async getUserPlaylists(): Promise<KugouPlaylist[]> {
    try {
      const res = await fetch(`${API_BASE}/playlist/user?source=kugou`);
      if (res.ok) {
        const d = await res.json();
        const list = Array.isArray(d.data) ? d.data : (Array.isArray(d) ? d : []);
        if (list.length > 0) {
          return list.map((item: any, idx: number) => ({
            id: String(item.id || item.specialid || idx),
            name: item.name || item.title || (idx === 0 ? '我喜欢的声音' : `极客歌单 #${idx}`),
            cover: item.cover || item.pic || 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300',
            count: item.count || item.song_count || 0,
            isFavorite: idx === 0 || !!item.is_favorite
          }));
        }
      }
    } catch (e) {
      console.warn('Failed to fetch user playlists, fallback to default profile playlists', e);
    }

    // 默认空列表（不塞死假数据）
    return [];
  }

  /**
   * 4. 获取指定歌单详情与歌曲列表
   */
  public async getPlaylistDetail(playlistId: string): Promise<{ playlist?: KugouPlaylist; songs: KugouSong[] }> {
    try {
      const res = await fetch(`${API_BASE}/playlist/detail?id=${encodeURIComponent(playlistId)}&source=kugou`);
      if (res.ok) {
        const d = await res.json();
        const rawSongs = d.data?.songs || d.songs || d.data || [];
        const songs: KugouSong[] = rawSongs.map((s: any) => ({
          id: s.id || s.hash || '',
          name: s.name || s.title || s.songname || '未知曲目',
          singer: s.singer || s.artist || s.singername || '未知歌手',
          album: s.album || s.album_name || '单曲原声',
          duration: s.duration || 240,
          cover: s.cover || s.pic || 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300',
          quality: (s.quality || 'SQ') as any
        }));
        return { songs };
      }
    } catch (e) {
      console.warn('Failed to fetch playlist detail', e);
    }
    return { songs: [] };
  }

  /**
   * 5. 全网歌曲搜索
   */
  public async searchSongs(keyword: string, page = 1, pageSize = 20): Promise<{ total: number; songs: KugouSong[] }> {
    const res = await fetch(`${API_BASE}/music/search?q=${encodeURIComponent(keyword)}&type=song&sources=kugou&page=${page}&limit=${pageSize}`);
    if (!res.ok) {
      throw new Error(`搜索失败: HTTP ${res.status}`);
    }
    const d = await res.json();
    const rawList = d.data?.songs || d.songs || d.data || [];
    const songs: KugouSong[] = rawList.map((s: any) => ({
      id: s.id || s.hash || '',
      name: s.name || s.title || s.songname || keyword,
      singer: s.singer || s.artist || s.singername || '酷狗歌手',
      album: s.album || s.album_name || '酷狗原声',
      duration: s.duration || 240,
      cover: s.cover || s.pic || 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300',
      quality: (s.quality || 'SQ') as any
    }));
    return { total: d.data?.total || songs.length, songs };
  }

  /**
   * 6. 解析音频真实播放地址
   */
  public async getSongPlayUrl(songId: string, quality = '128'): Promise<string> {
    // 优先调用 go-music-api 的代理流播放接口，避免所有防盗链与 403 跨域问题
    return `${API_BASE}/music/stream?id=${encodeURIComponent(songId)}&source=kugou&quality=${quality}`;
  }

  /**
   * 7. 获取并解析歌词
   */
  public async getLyric(songId: string): Promise<LyricLine[]> {
    try {
      const res = await fetch(`${API_BASE}/music/lyric?id=${encodeURIComponent(songId)}&source=kugou`);
      if (res.ok) {
        const d = await res.json();
        const lrcText = d.data?.lrc || d.lrc || d.data || '';
        return this.parseLrc(lrcText);
      }
    } catch (e) {
      console.warn('Failed to fetch lyric', e);
    }
    return [];
  }

  /**
   * 解析标准 LRC 歌词文本为时间戳数组
   */
  public parseLrc(lrcText: string): LyricLine[] {
    if (!lrcText) return [];
    const lines = lrcText.split('\n');
    const result: LyricLine[] = [];
    const reg = /\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\](.*)/;

    for (const line of lines) {
      const match = reg.exec(line.trim());
      if (match) {
        const min = parseInt(match[1], 10);
        const sec = parseInt(match[2], 10);
        const ms = match[3] ? parseInt(match[3].padEnd(3, '0').slice(0, 3), 10) : 0;
        const totalSeconds = min * 60 + sec + ms / 1000;
        const text = match[4].trim();
        if (text) {
          result.push({ time: totalSeconds, text });
        }
      }
    }
    return result.sort((a, b) => a.time - b.time);
  }
}

export const kugouApi = new KugouApiClient();
