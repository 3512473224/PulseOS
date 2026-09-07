<template>
  <div class="kugou-music-hub w-full min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30">
    
    <!-- ======================================================== -->
    <!-- 1. 顶部：用户登录与状态栏 (Header Status Bar) -->
    <!-- ======================================================== -->
    <header class="sticky top-0 z-40 w-full backdrop-blur-xl bg-slate-900/70 border-b border-white/10 px-6 py-3 flex items-center justify-between shadow-2xl">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-[1px] shadow-lg shadow-blue-500/20">
          <div class="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center font-bold text-cyan-400 text-sm tracking-wider">
            KG
          </div>
        </div>
        <div>
          <h1 class="text-sm font-semibold tracking-wide bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-cyan-300">
            酷狗极客云音乐
          </h1>
          <p class="text-[11px] text-slate-400 font-mono">PulseOS Music Engine · 扫码直连中台</p>
        </div>
      </div>

      <!-- 中间：全网快速搜歌栏 -->
      <div class="hidden md:flex items-center w-80 relative">
        <input 
          v-model="searchKeyword"
          @keydown.enter="handleSearch"
          type="text" 
          placeholder="搜索全网歌曲、歌手、专辑..." 
          class="w-full bg-slate-800/60 border border-white/10 rounded-full py-1.5 pl-9 pr-4 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all"
        />
        <svg class="w-3.5 h-3.5 text-slate-400 absolute left-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <!-- 右侧：登录鉴权与用户状态 -->
      <div class="flex items-center gap-3">
        <!-- 未登录 -->
        <template v-if="!isLoggedIn">
          <button 
            @click="openLoginModal"
            class="group relative inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium text-cyan-300 bg-cyan-950/40 border border-cyan-500/30 hover:border-cyan-400 hover:shadow-lg hover:shadow-cyan-500/20 active:scale-95 transition-all"
          >
            <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
            <span>扫码登录酷狗</span>
          </button>
        </template>

        <!-- 已登录 -->
        <template v-else>
          <div class="flex items-center gap-3 bg-white/5 border border-white/10 rounded-full py-1 px-3">
            <img 
              :src="currentUser?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'" 
              alt="Avatar"
              class="w-6 h-6 rounded-full object-cover ring-1 ring-cyan-400/50"
            />
            <span class="text-xs font-medium text-slate-200">{{ currentUser?.nickname }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono">已认证</span>
            <button 
              @click="handleLogout"
              title="退出登录"
              class="text-slate-400 hover:text-red-400 text-xs ml-1 transition-colors"
            >
              ✕
            </button>
          </div>
        </template>
      </div>
    </header>

    <!-- ======================================================== -->
    <!-- 2. 中部：左侧歌单分类抽屉 + 右侧曲目详情表格 -->
    <!-- ======================================================== -->
    <main class="flex-1 flex overflow-hidden pb-24">
      
      <!-- 左侧：歌单分类抽屉 -->
      <aside class="w-64 border-r border-white/5 bg-slate-900/40 p-4 flex flex-col gap-4 shrink-0 overflow-y-auto">
        <div>
          <div class="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2 px-2">我的云端音乐</div>
          <div class="flex flex-col gap-1">
            <button 
              @click="selectPlaylist(favoritePlaylist)"
              :class="[
                'w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all text-left',
                activePlaylist?.id === favoritePlaylist.id 
                  ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm' 
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              ]"
            >
              <div class="flex items-center gap-2.5 truncate">
                <span class="text-rose-400">❤️</span>
                <span class="truncate">我喜欢的声音</span>
              </div>
              <span class="text-[10px] text-slate-500 font-mono">{{ favoritePlaylist.count }}</span>
            </button>
          </div>
        </div>

        <div>
          <div class="flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-2 px-2">
            <span>自建歌单</span>
            <button @click="fetchUserPlaylists" title="刷新歌单" class="hover:text-cyan-400 transition-colors">↻</button>
          </div>

          <div v-if="playlists.length === 0" class="px-3 py-6 text-center text-xs text-slate-500">
            <span v-if="!isLoggedIn">登录后同步您的专属歌单</span>
            <span v-else>暂无自建歌单</span>
          </div>

          <div v-else class="flex flex-col gap-1">
            <button 
              v-for="pl in playlists" 
              :key="pl.id"
              @click="selectPlaylist(pl)"
              :class="[
                'w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all text-left',
                activePlaylist?.id === pl.id 
                  ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm' 
                  : 'text-slate-300 hover:bg-white/5 hover:text-white'
              ]"
            >
              <div class="flex items-center gap-2.5 truncate">
                <img :src="pl.cover" class="w-6 h-6 rounded-md object-cover border border-white/10" />
                <span class="truncate">{{ pl.name }}</span>
              </div>
              <span class="text-[10px] text-slate-500 font-mono">{{ pl.count }}</span>
            </button>
          </div>
        </div>
      </aside>

      <!-- 右侧：歌曲列表表格 -->
      <section class="flex-1 flex flex-col overflow-y-auto bg-slate-950/50 p-6">
        
        <!-- 歌单头部 Banner -->
        <div class="flex items-end gap-5 mb-6 pb-6 border-b border-white/10">
          <img 
            :src="activePlaylist?.cover || 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300'" 
            class="w-24 h-24 rounded-2xl object-cover shadow-2xl ring-1 ring-white/10"
          />
          <div class="flex flex-col gap-2">
            <div class="flex items-center gap-2">
              <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">歌单</span>
              <span class="text-xs text-slate-400">{{ activePlaylist?.count || songs.length }} 首曲目</span>
            </div>
            <h2 class="text-2xl font-bold text-white tracking-tight">{{ activePlaylist?.name || '精选歌曲' }}</h2>
            <div class="flex items-center gap-3 text-xs text-slate-400">
              <button 
                @click="playAll"
                class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold shadow-lg shadow-cyan-500/20 active:scale-95 transition-all"
              >
                <span>▶</span>
                <span>播放全部</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 歌曲列表表格 -->
        <div class="w-full overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="border-b border-white/5 text-[11px] font-mono text-slate-400 uppercase">
              <tr>
                <th class="py-2.5 px-3 w-12 text-center">#</th>
                <th class="py-2.5 px-4">歌曲标题</th>
                <th class="py-2.5 px-4">歌手</th>
                <th class="py-2.5 px-4 hidden md:table-cell">专辑</th>
                <th class="py-2.5 px-3 w-20 text-center">音质</th>
                <th class="py-2.5 px-3 w-16 text-right">时长</th>
                <th class="py-2.5 px-4 w-20 text-center">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5">
              <tr 
                v-for="(song, idx) in songs" 
                :key="song.id || idx"
                @dblclick="playSong(song)"
                :class="[
                  'group hover:bg-white/[0.04] transition-colors cursor-pointer',
                  currentSong?.id === song.id ? 'bg-cyan-500/10 text-cyan-300' : ''
                ]"
              >
                <!-- 序号 / 播放指示 -->
                <td class="py-3 px-3 text-center font-mono text-slate-500 group-hover:text-cyan-400">
                  <span v-if="currentSong?.id === song.id && isPlaying" class="inline-block animate-pulse text-cyan-400">🔊</span>
                  <span v-else>{{ idx + 1 < 10 ? '0' + (idx + 1) : idx + 1 }}</span>
                </td>

                <!-- 歌名与封面 -->
                <td class="py-3 px-4">
                  <div class="flex items-center gap-3">
                    <img :src="song.cover" class="w-8 h-8 rounded-lg object-cover border border-white/10" />
                    <div class="truncate font-medium text-slate-200 group-hover:text-cyan-200">
                      {{ song.name }}
                    </div>
                  </div>
                </td>

                <!-- 歌手 -->
                <td class="py-3 px-4 text-slate-400 group-hover:text-slate-300">{{ song.singer }}</td>

                <!-- 专辑 -->
                <td class="py-3 px-4 text-slate-500 hidden md:table-cell truncate max-w-xs">{{ song.album }}</td>

                <!-- 品质标签 -->
                <td class="py-3 px-3 text-center">
                  <span class="px-1.5 py-0.5 rounded text-[10px] font-mono border border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
                    {{ song.quality || 'SQ' }}
                  </span>
                </td>

                <!-- 时长 -->
                <td class="py-3 px-3 text-right font-mono text-slate-400">
                  {{ formatTime(song.duration) }}
                </td>

                <!-- 操作按钮 -->
                <td class="py-3 px-4 text-center">
                  <button 
                    @click.stop="playSong(song)"
                    class="p-1.5 rounded-full bg-white/5 hover:bg-cyan-500 hover:text-slate-950 text-slate-300 transition-all shadow"
                  >
                    <span v-if="currentSong?.id === song.id && isPlaying">⏸</span>
                    <span v-else>▶</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="songs.length === 0" class="py-16 text-center text-xs text-slate-500 font-mono">
            未发现任何歌曲，可点击左侧歌单或顶部进行全网搜索
          </div>
        </div>
      </section>
    </main>

    <!-- ======================================================== -->
    <!-- 3. 底部：吸底半透明悬浮播放条 (Floating Glass Player Bar) -->
    <!-- ======================================================== -->
    <footer class="fixed bottom-0 left-0 right-0 z-50 h-20 bg-slate-900/80 backdrop-blur-2xl border-t border-white/10 px-6 flex items-center justify-between shadow-2xl">
      
      <!-- 左侧：封面旋转 + 歌名/歌手 -->
      <div class="flex items-center gap-3.5 w-64 min-w-0">
        <div class="relative w-12 h-12 rounded-full overflow-hidden border border-white/20 shadow-lg shadow-black/50 shrink-0">
          <img 
            :src="currentSong?.cover || 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=200'" 
            :class="['w-full h-full object-cover', isPlaying ? 'animate-spin' : '']"
            style="animation-duration: 16s;"
          />
          <div class="absolute inset-0 m-auto w-3 h-3 rounded-full bg-slate-950 border border-white/30"></div>
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold text-slate-100 truncate hover:text-cyan-300 transition-colors">
            {{ currentSong?.name || '静候心流之音' }}
          </div>
          <div class="text-[11px] text-slate-400 truncate">
            {{ currentSong?.singer || 'PulseOS 酷狗播放引擎' }}
          </div>
        </div>
      </div>

      <!-- 中间：播放控制 + 进度条 + 单行跑马灯歌词 -->
      <div class="flex-1 max-w-2xl px-6 flex flex-col items-center gap-1.5">
        
        <!-- 控制按钮组 -->
        <div class="flex items-center gap-4">
          <!-- 模式切换 -->
          <button 
            @click="togglePlayMode"
            :title="playMode === 'loop' ? '列表循环' : (playMode === 'single' ? '单曲循环' : '随机播放')"
            class="text-slate-400 hover:text-cyan-400 text-xs transition-colors"
          >
            <span v-if="playMode === 'loop'">🔁</span>
            <span v-else-if="playMode === 'single'">🔂</span>
            <span v-else>🔀</span>
          </button>

          <!-- 上一曲 -->
          <button @click="prevSong" class="text-slate-300 hover:text-white transition-colors text-sm">⏮</button>

          <!-- 播放/暂停大按键 -->
          <button 
            @click="togglePlay"
            class="w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 text-slate-950 flex items-center justify-center font-bold shadow-lg shadow-cyan-500/25 hover:scale-105 active:scale-95 transition-all"
          >
            <span v-if="isPlaying">⏸</span>
            <span v-else>▶</span>
          </button>

          <!-- 下一曲 -->
          <button @click="nextSong" class="text-slate-300 hover:text-white transition-colors text-sm">⏭</button>

          <!-- 歌词弹窗/抽屉开关 -->
          <button 
            @click="showLyricDrawer = !showLyricDrawer" 
            :class="['text-xs transition-colors', showLyricDrawer ? 'text-cyan-400' : 'text-slate-400 hover:text-white']"
            title="查看完整歌词"
          >
            词
          </button>
        </div>

        <!-- 进度条 -->
        <div class="w-full flex items-center gap-2.5 text-[10px] font-mono text-slate-400">
          <span>{{ formatTime(currentTime) }}</span>
          <div 
            ref="progressBar"
            @click="seekProgress"
            class="flex-1 h-1 bg-white/10 rounded-full overflow-hidden cursor-pointer relative group"
          >
            <div 
              class="h-full bg-gradient-to-r from-cyan-400 to-indigo-500 relative"
              :style="{ width: `${progressPercent}%` }"
            >
              <span class="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white opacity-0 group-hover:opacity-100 shadow transition-opacity"></span>
            </div>
          </div>
          <span>{{ formatTime(duration) }}</span>
        </div>

        <!-- 单行歌词跑马灯 -->
        <div class="h-4 text-[11px] text-cyan-300/90 font-medium tracking-wide truncate transition-all text-center">
          {{ currentLyricText || '代码即艺术，专注构建未来 ✨' }}
        </div>
      </div>

      <!-- 右侧：音量与辅助工具 -->
      <div class="flex items-center justify-end gap-3 w-64">
        <span class="text-xs text-slate-400">🔈</span>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.05" 
          v-model="volume" 
          @input="onVolumeChange"
          class="w-20 h-1 bg-white/10 rounded-lg accent-cyan-400 cursor-pointer"
        />
        <span class="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
          Hi-Res
        </span>
      </div>
    </footer>

    <!-- ======================================================== -->
    <!-- 4. 扫码登录 Modal 弹窗 -->
    <!-- ======================================================== -->
    <div 
      v-if="isLoginModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 transition-all"
      @click.self="closeLoginModal"
    >
      <div class="relative w-full max-w-sm rounded-3xl bg-slate-900/90 border border-white/15 p-6 shadow-2xl flex flex-col items-center text-center">
        <button 
          @click="closeLoginModal"
          class="absolute top-4 right-4 text-slate-400 hover:text-white text-xs w-7 h-7 rounded-full bg-white/5 flex items-center justify-center"
        >
          ✕
        </button>

        <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-bold text-xl mb-3 shadow-lg shadow-cyan-500/30">
          KG
        </div>
        <h3 class="text-base font-bold text-white mb-1">酷狗音乐扫码登录</h3>
        <p class="text-xs text-slate-400 mb-5">打开手机酷狗音乐 App [扫一扫] 快速授权</p>

        <!-- 二维码显示区 -->
        <div class="relative w-48 h-48 bg-white p-2.5 rounded-2xl shadow-inner flex items-center justify-center">
          <template v-if="qrSession?.qrUrl">
            <img 
              :src="`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(qrSession.qrUrl)}`" 
              alt="QR Code"
              class="w-full h-full object-contain"
            />
          </template>
          <template v-else>
            <div class="text-xs text-slate-500 font-mono animate-pulse">正在生成二维码...</div>
          </template>

          <!-- 遮罩提示（过期或确认中） -->
          <div 
            v-if="qrStatus === 'expired' || qrStatus === 'scanned'" 
            class="absolute inset-0 bg-slate-950/85 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center p-3"
          >
            <template v-if="qrStatus === 'expired'">
              <span class="text-red-400 text-xs mb-2">二维码已过期</span>
              <button 
                @click="generateQR" 
                class="px-3 py-1 bg-cyan-500 text-slate-950 text-xs font-semibold rounded-full hover:bg-cyan-400 transition-all"
              >
                点击刷新
              </button>
            </template>
            <template v-else-if="qrStatus === 'scanned'">
              <span class="text-cyan-400 text-xs font-medium animate-bounce">📱 扫码成功</span>
              <span class="text-[11px] text-slate-300 mt-1">请在手机端点击【确认登录】</span>
            </template>
          </div>
        </div>

        <!-- 状态提示文字 -->
        <div class="mt-4 flex items-center gap-2 text-xs text-slate-400 font-mono">
          <span 
            :class="[
              'w-2 h-2 rounded-full',
              qrStatus === 'waiting' ? 'bg-cyan-400 animate-ping' : (qrStatus === 'scanned' ? 'bg-amber-400' : 'bg-slate-500')
            ]"
          ></span>
          <span>{{ qrMessage }}</span>
        </div>
      </div>
    </div>

    <!-- 隐藏的真实音频引擎 -->
    <audio 
      ref="audioPlayer" 
      @timeupdate="onTimeUpdate"
      @ended="onTrackEnded"
      @canplay="onCanPlay"
      preload="auto"
    ></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { kugouApi, type UserProfile, type KugouPlaylist, type KugouSong, type QRLoginSession, type LyricLine } from './kugouApi';

// ==========================================
// 响应式状态管理
// ==========================================
const currentUser = ref<UserProfile | null>(null);
const isLoggedIn = computed(() => !!currentUser.value);

// 歌单与歌曲
const favoritePlaylist = ref<KugouPlaylist>({
  id: 'favorites',
  name: '我喜欢的声音',
  cover: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300',
  count: 0,
  isFavorite: true
});
const playlists = ref<KugouPlaylist[]>([]);
const activePlaylist = ref<KugouPlaylist | null>(null);
const songs = ref<KugouSong[]>([]);
const searchKeyword = ref('');

// 播放器状态
const audioPlayer = ref<HTMLAudioElement | null>(null);
const currentSong = ref<KugouSong | null>(null);
const currentTrackIdx = ref(0);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const volume = ref(0.85);
const playMode = ref<'loop' | 'single' | 'random'>('loop');
const lyrics = ref<LyricLine[]>([]);
const showLyricDrawer = ref(false);

const progressPercent = computed(() => {
  if (!duration.value) return 0;
  return (currentTime.value / duration.value) * 100;
});

const currentLyricText = computed(() => {
  if (lyrics.value.length === 0) return '';
  const cur = currentTime.value;
  let target = '';
  for (let i = 0; i < lyrics.value.length; i++) {
    if (cur >= lyrics.value[i].time) {
      target = lyrics.value[i].text;
    } else {
      break;
    }
  }
  return target;
});

// 扫码弹窗与轮询状态
const isLoginModalOpen = ref(false);
const qrSession = ref<QRLoginSession | null>(null);
const qrStatus = ref<'waiting' | 'scanned' | 'success' | 'expired' | 'failed'>('waiting');
const qrMessage = ref('等待扫码...');
let pollTimer: any = null;

// ==========================================
// 生命周期与初始化
// ==========================================
onMounted(() => {
  currentUser.value = kugouApi.loadUserFromStorage();
  if (isLoggedIn.value) {
    fetchUserPlaylists();
  }
  // 默认选定我喜欢
  activePlaylist.value = favoritePlaylist.value;
});

onUnmounted(() => {
  stopPoll();
});

// ==========================================
// 业务逻辑：扫码登录与轮询
// ==========================================
async function openLoginModal() {
  isLoginModalOpen.value = true;
  await generateQR();
}

function closeLoginModal() {
  isLoginModalOpen.value = false;
  stopPoll();
}

async function generateQR() {
  stopPoll();
  qrStatus.value = 'waiting';
  qrMessage.value = '请使用酷狗音乐 App 扫码';
  try {
    qrSession.value = await kugouApi.createQRLogin();
    startPoll(qrSession.value.key);
  } catch (e: any) {
    qrStatus.value = 'failed';
    qrMessage.value = e.message || '二维码生成失败';
  }
}

function startPoll(key: string) {
  stopPoll();
  pollTimer = setInterval(async () => {
    try {
      const res = await kugouApi.checkQRLogin(key);
      qrStatus.value = res.status;
      qrMessage.value = res.message;

      if (res.status === 'success' && res.user) {
        currentUser.value = res.user;
        stopPoll();
        setTimeout(() => {
          closeLoginModal();
          fetchUserPlaylists();
        }, 1000);
      } else if (res.status === 'expired' || res.status === 'failed') {
        stopPoll();
      }
    } catch (e) {
      console.warn('QR poll error', e);
    }
  }, 2000);
}

function stopPoll() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function handleLogout() {
  kugouApi.logout();
  currentUser.value = null;
  playlists.value = [];
  songs.value = [];
}

// ==========================================
// 业务逻辑：歌单与曲目检索
// ==========================================
async function fetchUserPlaylists() {
  try {
    const list = await kugouApi.getUserPlaylists();
    playlists.value = list;
    if (list.length > 0) {
      favoritePlaylist.value.count = list[0].count;
    }
  } catch (e) {
    console.warn('Fetch playlists failed', e);
  }
}

async function selectPlaylist(pl: KugouPlaylist) {
  activePlaylist.value = pl;
  try {
    const res = await kugouApi.getPlaylistDetail(pl.id);
    songs.value = res.songs;
  } catch (e) {
    console.warn('Load playlist detail failed', e);
  }
}

async function handleSearch() {
  const kw = searchKeyword.value.trim();
  if (!kw) return;
  try {
    const res = await kugouApi.searchSongs(kw);
    songs.value = res.songs;
    activePlaylist.value = {
      id: 'search',
      name: `搜索结果: "${kw}"`,
      cover: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300',
      count: res.songs.length,
      isFavorite: false
    };
  } catch (e) {
    console.warn('Search failed', e);
  }
}

// ==========================================
// 业务逻辑：音频播放与控制
// ==========================================
async function playSong(song: KugouSong) {
  currentSong.value = song;
  const idx = songs.value.findIndex(s => s.id === song.id);
  if (idx !== -1) currentTrackIdx.value = idx;

  // 获取真实流媒体播放地址
  const playUrl = await kugouApi.getSongPlayUrl(song.id);
  
  if (audioPlayer.value) {
    audioPlayer.value.src = playUrl;
    audioPlayer.value.play().then(() => {
      isPlaying.value = true;
    }).catch(e => {
      console.warn('Play error:', e);
    });
  }

  // 加载歌词
  lyrics.value = await kugouApi.getLyric(song.id);
}

function playAll() {
  if (songs.value.length > 0) {
    playSong(songs.value[0]);
  }
}

function togglePlay() {
  if (!audioPlayer.value || !currentSong.value) return;
  if (isPlaying.value) {
    audioPlayer.value.pause();
    isPlaying.value = false;
  } else {
    audioPlayer.value.play();
    isPlaying.value = true;
  }
}

function prevSong() {
  if (songs.value.length === 0) return;
  let nextIdx = currentTrackIdx.value - 1;
  if (nextIdx < 0) nextIdx = songs.value.length - 1;
  playSong(songs.value[nextIdx]);
}

function nextSong() {
  if (songs.value.length === 0) return;
  let nextIdx = 0;
  if (playMode.value === 'random') {
    nextIdx = Math.floor(Math.random() * songs.value.length);
  } else {
    nextIdx = (currentTrackIdx.value + 1) % songs.value.length;
  }
  playSong(songs.value[nextIdx]);
}

function togglePlayMode() {
  if (playMode.value === 'loop') playMode.value = 'single';
  else if (playMode.value === 'single') playMode.value = 'random';
  else playMode.value = 'loop';
}

function onTimeUpdate() {
  if (audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime;
    duration.value = audioPlayer.value.duration || 0;
  }
}

function onCanPlay() {
  if (audioPlayer.value) {
    duration.value = audioPlayer.value.duration || 0;
  }
}

function onTrackEnded() {
  if (playMode.value === 'single') {
    if (audioPlayer.value) {
      audioPlayer.value.currentTime = 0;
      audioPlayer.value.play();
    }
  } else {
    nextSong();
  }
}

function seekProgress(e: MouseEvent) {
  const bar = e.currentTarget as HTMLElement;
  if (!bar || !audioPlayer.value || !duration.value) return;
  const rect = bar.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const newTime = (clickX / rect.width) * duration.value;
  audioPlayer.value.currentTime = newTime;
  currentTime.value = newTime;
}

function onVolumeChange() {
  if (audioPlayer.value) {
    audioPlayer.value.volume = Number(volume.value);
  }
}

function formatTime(secs: number): string {
  if (isNaN(secs) || secs < 0) return '00:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m < 10 ? '0' + m : m}:${s < 10 ? '0' + s : s}`;
}
</script>

<style scoped>
/* Glassmorphism 与平滑旋转动效 */
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin-slow 16s linear infinite;
}
</style>
