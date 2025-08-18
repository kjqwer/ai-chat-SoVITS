<template>
    <div class="chat-page">
        <div class="chat-container">
            <!-- 左侧对话列表 -->
            <ConversationSidebar @showExportDialog="showExportDialog = true" />

            <!-- 右侧聊天区域 -->
            <div class="chat-main">
                <!-- 聊天头部 -->
                <div class="chat-header">
                    <div class="chat-title">
                        <h3>{{ currentConversation?.title || 'AI对话' }}</h3>
                        <div class="chat-info">
                            <span v-if="currentConversation">
                                当前人格: {{ currentConversation.persona.name }}
                            </span>
                        </div>
                    </div>
                    <div class="chat-controls">
                        <div class="control-group">
                            <el-switch v-model="speechRecognitionEnabled" active-text="语音识别" inactive-text=""
                                size="small" />
                        </div>
                        <div class="control-group">
                            <el-switch v-model="chatStore.autoGenerateAudio" active-text="自动语音" inactive-text=""
                                size="small" @change="chatStore.toggleAutoGenerateAudio" />
                        </div>
                        <div class="control-group">
                            <el-switch v-model="autoPlayAudio" active-text="自动播放" inactive-text="" size="small"
                                @change="toggleAutoPlayAudio" />
                        </div>
                    </div>
                </div>

                <!-- 消息列表 -->
                <MessageList ref="messageListRef" @generateAudio="generateAudio"
                    @switchAudioVersion="switchAudioVersion" @deleteAudioVersion="deleteAudioVersion"
                    @regenerateResponse="regenerateResponse" @rollbackToMessage="rollbackToMessage"
                    @deleteMessage="deleteMessage" />

                <!-- 输入区域 -->
                <MessageInput ref="messageInputRef" :speechRecognitionEnabled="speechRecognitionEnabled"
                    @sendMessage="sendMessage" 
                    @audioPlaybackStarted="handleRealtimeAudioPlaybackStarted"
                    @audioPlaybackEnded="handleRealtimeAudioPlaybackEnded" />
            </div>
        </div>

        <!-- 批量导出对话框 -->
        <ExportDialog v-model="showExportDialog" />
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '../stores/chat.js'
import { useApiStore } from '../stores/api.js'
import ConversationSidebar from './ChatPage/ConversationSidebar.vue'
import MessageList from './ChatPage/MessageList.vue'
import MessageInput from './ChatPage/MessageInput.vue'
import ExportDialog from './ChatPage/ExportDialog.vue'

const chatStore = useChatStore()
const apiStore = useApiStore()

// 响应式数据
const showExportDialog = ref(false)
const speechRecognitionEnabled = ref(true)
const autoPlayAudio = ref(true)
const currentPlayingAudio = ref(null)

// 组件引用
const messageListRef = ref(null)
const messageInputRef = ref(null)

// 计算属性
const currentConversation = computed(() => chatStore.currentConversation)

// 发送消息
const sendMessage = async (messageText) => {
    try {
        await chatStore.sendMessage(messageText)

        // 滚动到底部
        await nextTick()
        messageListRef.value?.scrollToBottom()

        // 如果开启了自动语音生成和自动播放，监听新消息的音频生成
        if (chatStore.autoGenerateAudio && autoPlayAudio.value) {
            const currentConv = chatStore.currentConversation
            if (currentConv && currentConv.messages.length > 0) {
                const lastMessage = currentConv.messages[currentConv.messages.length - 1]

                // 如果是AI消息且有音频生成
                if (lastMessage.role === 'assistant') {
                    // 等待音频生成完成后自动播放
                    const checkAudioGeneration = () => {
                        // 重新获取最新的对话数据
                        const updatedConv = chatStore.conversations.find(conv => conv.id === currentConv.id)
                        if (updatedConv) {
                            const updatedMessage = updatedConv.messages.find(msg => msg.id === lastMessage.id)
                            if (updatedMessage) {
                                if (updatedMessage.audioVersions?.length > 0 && !updatedMessage.audioGenerating) {
                                    const currentVersion = updatedMessage.currentAudioVersion >= 0 ? updatedMessage.currentAudioVersion : 0
                                    const audioUrl = updatedMessage.audioVersions[currentVersion]?.url
                                    if (audioUrl) {
                                        autoPlayGeneratedAudio(audioUrl)
                                        return // 找到音频，停止检查
                                    }
                                } else if (updatedMessage.audioGenerating) {
                                    // 如果还在生成中，继续等待
                                    setTimeout(checkAudioGeneration, 1000)
                                    return
                                }
                            }
                        }
                        
                        // 如果检查了10次（10秒）还没有音频，停止检查
                        if (checkAudioGeneration.count === undefined) {
                            checkAudioGeneration.count = 0
                        }
                        checkAudioGeneration.count++
                        
                        if (checkAudioGeneration.count < 10) {
                            setTimeout(checkAudioGeneration, 1000)
                        }
                    }

                    // 延迟检查，给音频生成一些时间
                    setTimeout(checkAudioGeneration, 2000)
                }
            }
        }
    } catch (error) {
        ElMessage.error(`发送消息失败: ${error.message}`)
    }
}

// 生成音频
const generateAudio = async (conversationId, messageId, isRegenerate = false) => {
    try {
        await chatStore.generateMessageAudio(conversationId, messageId, isRegenerate)
        ElMessage.success('语音生成成功')

        // 如果开启了自动播放，播放最新生成的音频
        if (autoPlayAudio.value) {
            // 等待一下让后端数据更新完成
            setTimeout(async () => {
                // 重新加载对话数据以确保获取最新的音频版本
                await chatStore.loadConversations()
                
                const message = chatStore.conversations
                    .find(conv => conv.id === conversationId)?.messages
                    .find(msg => msg.id === messageId)

                if (message?.audioVersions?.length > 0) {
                    // 播放最新生成的音频版本（最后一个版本）
                    const latestVersionIndex = message.audioVersions.length - 1
                    const audioUrl = message.audioVersions[latestVersionIndex]?.url
                    if (audioUrl) {
                        console.log('自动播放最新生成的音频:', audioUrl)
                        autoPlayGeneratedAudio(audioUrl)
                    }
                }
            }, 1000) // 等待1秒确保后端数据更新完成
        }
    } catch (error) {
        ElMessage.error('语音生成失败')
    }
}

// 切换音频版本
const switchAudioVersion = async (conversationId, messageId, versionIndex) => {
    try {
        await chatStore.switchAudioVersion(conversationId, messageId, versionIndex)
        ElMessage.success('已切换到语音版本')
    } catch (error) {
        ElMessage.error('切换语音版本失败')
    }
}

// 删除音频版本
const deleteAudioVersion = async (conversationId, messageId, versionIndex) => {
    try {
        await ElMessageBox.confirm(
            `确定要删除语音版本 ${versionIndex + 1} 吗？这将删除该版本的所有音频文件。`,
            '确认删除',
            { type: 'warning' }
        )
        await chatStore.deleteAudioVersion(conversationId, messageId, versionIndex)
        ElMessage.success('语音版本已删除')
    } catch (error) {
        if (error !== 'cancel') {
            ElMessage.error('删除语音版本失败')
        }
    }
}

// 重新生成回复
const regenerateResponse = async (messageIndex) => {
    try {
        await chatStore.regenerateResponse(chatStore.currentConversationId, messageIndex)
        await nextTick()
        messageListRef.value?.scrollToBottom()
    } catch (error) {
        ElMessage.error('重新生成失败')
    }
}

// 回溯到消息
const rollbackToMessage = async (messageIndex) => {
    try {
        await ElMessageBox.confirm(
            `确定要回溯到第 ${messageIndex + 1} 条消息吗？这将删除后面的所有消息。`,
            '确认回溯',
            { type: 'warning' }
        )

        chatStore.rollbackToMessage(chatStore.currentConversationId, messageIndex)
        ElMessage.success('已回溯到指定消息')
    } catch {
        // 用户取消
    }
}

// 删除消息
const deleteMessage = async (messageIndex) => {
    try {
        await ElMessageBox.confirm('确定要删除这条消息吗？', '确认删除', {
            type: 'warning'
        })

        chatStore.deleteMessage(chatStore.currentConversationId, messageIndex)
        ElMessage.success('消息已删除')
    } catch {
        // 用户取消
    }
}

// 切换自动播放音频
const toggleAutoPlayAudio = () => {
    autoPlayAudio.value = !autoPlayAudio.value
    ElMessage.info(autoPlayAudio.value ? '已开启自动播放语音' : '已关闭自动播放语音')
}

// 自动播放音频
const autoPlayGeneratedAudio = (audioUrl) => {
    if (!autoPlayAudio.value) return

    try {
        // 停止当前播放的音频
        if (currentPlayingAudio.value) {
            currentPlayingAudio.value.pause()
            currentPlayingAudio.value.currentTime = 0
        }

        // 处理音频URL
        const fullAudioUrl = audioUrl.startsWith('/') ? `${window.location.origin}${audioUrl}` : audioUrl

        // 创建新的Audio对象并播放
        const audio = new Audio(fullAudioUrl)
        currentPlayingAudio.value = audio

        audio.onended = () => {
            currentPlayingAudio.value = null
        }

        audio.onerror = (error) => {
            console.error('音频播放失败:', error)
            currentPlayingAudio.value = null
        }

        audio.play().catch(error => {
            console.error('音频自动播放失败:', error)
            // 浏览器阻止自动播放时的处理
        })
    } catch (error) {
        console.error('音频播放出错:', error)
    }
}

// 处理实时语音音频播放开始
const handleRealtimeAudioPlaybackStarted = () => {
    console.log('实时语音：音频播放开始')
    // 设置全局音频播放状态
    window.isRealtimeAudioPlaying = true
}

// 处理实时语音音频播放结束
const handleRealtimeAudioPlaybackEnded = () => {
    console.log('实时语音：音频播放结束')
    // 清除全局音频播放状态
    window.isRealtimeAudioPlaying = false
}

// 清理资源
const cleanup = () => {
    // 清理音频播放
    if (currentPlayingAudio.value) {
        currentPlayingAudio.value.pause()
        currentPlayingAudio.value = null
    }

    // 清理录音资源
    messageInputRef.value?.cleanupRecording()
}

// 组件卸载时清理
onUnmounted(() => {
    cleanup()
    window.removeEventListener('beforeunload', cleanup)
})

// 组件挂载时初始化配置并创建第一个对话（如果没有的话）
onMounted(async () => {
    await chatStore.initializeChatStore()

    // 初始化API数据
    try {
        await apiStore.initializeData()
        console.log('API数据初始化完成')
    } catch (error) {
        console.warn('API数据初始化失败:', error)
    }

    // 从后端加载对话数据
    try {
        await chatStore.loadConversations()
        console.log('对话数据加载完成')
    } catch (error) {
        console.warn('对话数据加载失败:', error)
        // 如果加载失败，创建一个新对话
        if (chatStore.conversations.length === 0) {
            await chatStore.createConversationWithCurrentPersona('欢迎对话')
        }
    }

    // 初始化ASR功能
    try {
        await apiStore.initializeAsrData()
        console.log('ASR功能初始化完成')
    } catch (error) {
        console.warn('ASR功能初始化失败:', error)
        speechRecognitionEnabled.value = false
    }

    // 监听页面离开，清理资源
    window.addEventListener('beforeunload', cleanup)
})
</script>

<style scoped>
.chat-page {
    height: 100vh;
    background-color: #f5f5f5;
}

.chat-container {
    display: flex;
    height: 100%;
}

/* 聊天主区域 */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: white;
}

.chat-header {
    padding: 20px;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-title h3 {
    margin: 0 0 5px 0;
    color: #303133;
}

.chat-info {
    font-size: 14px;
    color: #909399;
}

.chat-controls {
    display: flex;
    align-items: center;
    gap: 15px;
}

.control-group {
    display: flex;
    align-items: center;
}
</style>