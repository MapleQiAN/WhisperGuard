<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <h1>🛡️ WhisprGuard 语义隐私助手</h1>
      </el-header>
      
      <el-main>
        <el-card class="analysis-card">
          <template #header>
            <div class="card-header">
              <span>文本风险分析</span>
              <div class="model-selector">
                <el-select v-model="selectedModel" placeholder="选择AI模型" @change="handleModelChange">
                  <el-option label="OpenAI" value="openai" />
                  <el-option label="DeepSeek" value="deepseek" />
                  <el-option label="Ollama" value="ollama" />
                </el-select>
                <el-select 
                  v-if="selectedModel === 'ollama'" 
                  v-model="selectedOllamaModel" 
                  placeholder="选择Ollama模型"
                  class="ollama-model-select"
                >
                  <el-option label="Qwen 7B" value="qwen:7b" />
                  <el-option label="Qwen 14B" value="qwen:14b" />
                  <el-option label="Llama2 7B" value="llama2:7b" />
                  <el-option label="Llama2 13B" value="llama2:13b" />
                  <el-option label="Mistral 7B" value="mistral:7b" />
                </el-select>
              </div>
            </div>
          </template>
          
          <el-form>
            <el-form-item>
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="6"
                placeholder="请输入需要分析的文本..."
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="analyzeText" :loading="loading">
                开始分析
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="analysisResult" class="result-card">
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
              <el-tag :type="getRiskLevelType(analysisResult.risk_level)">
                {{ analysisResult.risk_level }}风险
              </el-tag>
            </div>
          </template>

          <div class="result-content">
            <div class="result-section">
              <h3>敏感词</h3>
              <el-tag
                v-for="word in analysisResult.sensitive_words"
                :key="word"
                class="sensitive-word"
                type="danger"
              >
                {{ word }}
              </el-tag>
            </div>

            <div class="result-section">
              <h3>风险原因</h3>
              <p>{{ analysisResult.risk_reason }}</p>
            </div>

            <div class="result-section">
              <h3>改写建议</h3>
              <el-card
                v-for="(suggestion, index) in analysisResult.rewrite"
                :key="index"
                class="suggestion-card"
              >
                {{ suggestion }}
              </el-card>
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const inputText = ref('')
const selectedModel = ref('openai')
const selectedOllamaModel = ref('qwen:7b')
const loading = ref(false)
const analysisResult = ref(null)

const handleModelChange = (value) => {
  if (value !== 'ollama') {
    selectedOllamaModel.value = 'qwen:7b'
  }
}

const getRiskLevelType = (level) => {
  const types = {
    '低': 'success',
    '中': 'warning',
    '高': 'danger'
  }
  return types[level] || 'info'
}

const analyzeText = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入需要分析的文本')
    return
  }

  loading.value = true
  try {
    const response = await axios.post('/api/analyze', {
      text: inputText.value,
      model: selectedModel.value,
      ollama_model: selectedOllamaModel.value
    })
    analysisResult.value = response.data
  } catch (error) {
    ElMessage.error('分析失败：' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.el-header {
  text-align: center;
  padding: 20px 0;
  color: #409EFF;
}

.analysis-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-card {
  margin-top: 20px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-section {
  margin-bottom: 20px;
}

.result-section h3 {
  margin-bottom: 10px;
  color: #606266;
}

.sensitive-word {
  margin-right: 8px;
  margin-bottom: 8px;
}

.suggestion-card {
  margin-bottom: 10px;
  background-color: #f5f7fa;
}

.model-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.ollama-model-select {
  width: 150px;
}
</style> 