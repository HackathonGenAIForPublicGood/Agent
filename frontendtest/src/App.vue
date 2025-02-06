<template>
  <div class="container fr-container">
    <div class="fr-grid-row">
      <h1>3A - Analyseur d'Actes Administratifs</h1>

      <div class="fr-callout fr-icon-information-line">
        <h3 class="fr-callout__title">Bienvenue sur le 3A</h3>
        <p class="fr-callout__text">
          Le 3A est un outil d'analyse d'actes administratifs. Il permet d'extraire le texte d'un document PDF,
          d'analyser
          la forme du document, de le catégoriser en vue de son instruction par les Agents des préfectures, et de
          confronter le contenu aux textes juridiques dans le but de proposer une première analyse de la validité de
          l'acte.
        </p>
        <p class="fr-callout__text">
          Son utilisation a été voulue pour être très simple :
        <ul>
          <li>
            téléverser le document
          </li>
          <li>
            consulter les résultats
          </li>
        </ul>
        </p>
      </div>
    </div>
    <!-- Sélection du fichier -->
    <div class="fr-grid-row">
      <div class="fr-grid-col-12">
        <h3>Téléverser le document</h3>
        <div class="fr-upload-group">
          <label class="fr-label" for="file-upload-multiple">Ajouter le fichier à analyser :
            <span class="fr-hint-text">Taille maximale : 200 Mo. Formats supportés : pdf.</span>
          </label>

          <input type="file" @change="handleFileUpload" accept=".pdf" :disabled="isProcessing" class="fr-upload">
          <div v-if="selectedFile" class="file-info">
            Fichier sélectionné : {{ selectedFile.name }}
          </div>
        </div>
      </div>
    </div>

    <!-- Barres de progression -->
    <div class="fr-grid-row">
      <h3>Résultats de l'analyse</h3>
      <div class="progress-section">
        <div v-if="showTextProgress" class="task">
          <span>Extraction du texte</span>
          <div class="progress-bar">
            <div :style="{ width: textExtractionProgress + '%' }" class="progress"></div>
          </div>
          <span>{{ textExtractionProgress }}%</span>
        </div>

        <div v-if="showAnalysisProgress" class="task">
          <span>Analyse de forme</span>
          <div class="progress-bar">
            <div :style="{ width: analysisProgress + '%' }" class="progress"></div>
          </div>
          <span>{{ analysisProgress }}%</span>
        </div>

        <div v-if="showCategorizationProgress" class="task">
          <span>Catégorisation</span>
          <div class="progress-bar">
            <div :style="{ width: categorizationProgress + '%' }" class="progress"></div>
          </div>
          <span>{{ categorizationProgress }}%</span>
        </div>

        <div v-if="showValidityProgress" class="task">
          <span>Analyse de validité</span>
          <div class="progress-bar">
            <div :style="{ width: validityProgress + '%' }" class="progress"></div>
          </div>
          <span>{{ validityProgress }}%</span>
        </div>
      </div>

      <!-- Résultats -->
      <div v-if="results.text || results.analysis || results.categories" class="results-section">
        <div v-if="results.text" class="result-box">
          <h3>Texte extrait</h3>
          <div class="text-content">{{ results.text }}</div>
        </div>

        <div v-if="results.analysis" class="result-box">
          <h3>Analyse de forme</h3>

          <div class="analysis-header">
            <div class="analysis-meta">
              <p><strong>Type de document :</strong> {{ results.analysis.type_de_document }}</p>
              <p><strong>Collectivité :</strong> {{ results.analysis.collectivite }}</p>
              <p><strong>Signataire :</strong> {{ results.analysis.signataire }}</p>
              <p><strong>Niveau de confiance :</strong> {{ results.analysis.niveau_de_confiance }}</p>
            </div>
            <div class="analysis-observation">
              <p><strong>Observation générale :</strong></p>
              <p>{{ results.analysis.Observation }}</p>
            </div>
          </div>

          <div class="conformite-section">
            <h4>Conformité aux exigences légales</h4>
            <div class="conformite-grid">
              <div v-for="(value, key) in results.analysis.conformite_aux_exigences_legales" :key="key"
                class="conformite-item">
                <div class="conformite-header">
                  <span class="conformite-title">{{ formatTitle(key) }}</span>
                  <span :class="['conformite-status', value.etat]">
                    {{ value.etat }}
                  </span>
                </div>
                <p class="conformite-explanation">{{ value.explication }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="results.categories" class="result-box">
          <h3>Catégorisation</h3>
          <div class="categories-grid">
            <div v-for="(category, index) in results.categories" :key="index" class="category-item">
              <div class="category-header">
                <div class="category-titles">
                  <h4>{{ category.main_category.name }}</h4>
                  <p class="subcategory">{{ category.sub_category.name }}</p>
                </div>
                <span class="confidence-badge">
                  {{ formatConfidence(category.confidence) }}%
                </span>
              </div>
              <p class="category-explanation">{{ category.explanation }}</p>
            </div>
          </div>
        </div>

        <div v-if="results.validity" class="result-box">
          <h3>Analyse de validité juridique</h3>
          <div class="validity-content">
            <div class="validity-header">
              <div class="confidence-section">
                <h4>Indice de confiance</h4>
                <div class="confidence-indicator">
                  <div class="confidence-value">{{ extractConfidence(results.validity.analyse) }}%</div>
                  <div class="confidence-bar">
                    <div :style="{ width: extractConfidence(results.validity.analyse) + '%' }"
                      class="confidence-progress">
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="validity-body" v-html="formatMarkdown(results.validity.analyse)"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import { marked } from 'marked'

export default {
  name: 'App',
  setup() {
    const selectedFile = ref(null)
    const showTextProgress = ref(false)
    const showAnalysisProgress = ref(false)
    const showCategorizationProgress = ref(false)
    const showValidityProgress = ref(false)
    const textExtractionProgress = ref(0)
    const analysisProgress = ref(0)
    const categorizationProgress = ref(0)
    const validityProgress = ref(0)
    const results = ref({
      text: null,
      analysis: null,
      categories: null,
      validity: null
    })

    const handleFileUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      selectedFile.value = file
      resetProgress()

      try {
        // Upload du fichier et extraction du texte
        showTextProgress.value = true
        const formData = new FormData()
        formData.append('file', file)
        textExtractionProgress.value = 30
        const textResponse = await axios.post('http://localhost:8000/upload', formData)
        textExtractionProgress.value = 100
        results.value.text = textResponse.data.texte
        showTextProgress.value = false

        // Lancement indépendant de l'analyse, de la catégorisation et de la validité
        processAnalysis(textResponse.data.texte).catch(error => {
          console.error('Erreur analyse:', error)
          alert('Erreur lors de l\'analyse')
        })

        processCategories(textResponse.data.texte).catch(error => {
          console.error('Erreur catégorisation:', error)
          alert('Erreur lors de la catégorisation')
        })

        processValidity(textResponse.data.texte).catch(error => {
          console.error('Erreur validité:', error)
          alert('Erreur lors de l\'analyse de validité')
        })

      } catch (error) {
        console.error('Erreur extraction:', error)
        alert('Erreur lors de l\'extraction du texte')
        showTextProgress.value = false
      }
    }

    const processAnalysis = async (text) => {
      console.log("processAnalysis")
      showAnalysisProgress.value = true
      analysisProgress.value = 30
      try {
        const response = await axios.post('http://localhost:8000/analyser', { texte: text }, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        results.value.analysis = response.data
        analysisProgress.value = 100
        setTimeout(() => {
          showAnalysisProgress.value = false
        }, 500) // Petit délai pour voir le 100%
      } catch (error) {
        analysisProgress.value = 0
        console.error("Erreur détaillée /analyser:", error.response?.data)
        showAnalysisProgress.value = false
        throw error
      }
    }

    const processCategories = async (text) => {
      console.log("processCategories")
      showCategorizationProgress.value = true
      categorizationProgress.value = 30
      try {
        const response = await axios.post('http://localhost:8000/categoriser', { texte: text }, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        results.value.categories = response.data
        categorizationProgress.value = 100
        setTimeout(() => {
          showCategorizationProgress.value = false
        }, 500) // Petit délai pour voir le 100%
      } catch (error) {
        categorizationProgress.value = 0
        console.error("Erreur détaillée /categoriser:", error.response?.data)
        showCategorizationProgress.value = false
        throw error
      }
    }

    const processValidity = async (text) => {
      console.log("processValidity")
      showValidityProgress.value = true
      validityProgress.value = 30
      try {
        const response = await axios.post('http://localhost:8000/analyser-validite', { texte: text }, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        results.value.validity = response.data
        validityProgress.value = 100
        setTimeout(() => {
          showValidityProgress.value = false
        }, 500)
      } catch (error) {
        validityProgress.value = 0
        console.error("Erreur détaillée /analyser-validite:", error.response?.data)
        showValidityProgress.value = false
        throw error
      }
    }

    const resetProgress = () => {
      showTextProgress.value = false
      showAnalysisProgress.value = false
      showCategorizationProgress.value = false
      showValidityProgress.value = false
      textExtractionProgress.value = 0
      analysisProgress.value = 0
      categorizationProgress.value = 0
      validityProgress.value = 0
      results.value = {
        text: null,
        analysis: null,
        categories: null,
        validity: null
      }
    }

    const formatTitle = (key) => {
      return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    }

    const formatConfidence = (confidence) => {
      return Math.round(confidence * 100)
    }

    const extractConfidence = (text) => {
      const match = text.match(/Indice de confiance\s*:\s*(\d+)%?/)
      return match ? parseInt(match[1]) : 0
    }

    const formatMarkdown = (text) => {
      if (!text) return ''
      // Remplacer les ** par des balises strong pour le gras
      text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      return marked(text)
    }

    return {
      selectedFile,
      showTextProgress,
      showAnalysisProgress,
      showCategorizationProgress,
      showValidityProgress,
      textExtractionProgress,
      analysisProgress,
      categorizationProgress,
      validityProgress,
      results,
      handleFileUpload,
      formatConfidence,
      formatTitle,
      extractConfidence,
      formatMarkdown
    }
  }
}
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.upload-section {
  margin: 20px 0;
  padding: 20px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  text-align: center;
}

.progress-section {
  margin: 20px 0;
}

.task {
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex-grow: 1;
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

.results-section {
  margin-top: 30px;
}

.result-box {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.text-content {
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.category-item {
  margin: 10px 0;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
}

h1 {
  color: #2c3e50;
  text-align: center;
}

h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.file-info {
  margin-top: 10px;
  color: #666;
}

.analysis-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.analysis-meta p {
  margin: 5px 0;
}

.analysis-observation {
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
  border-left: 4px solid #4CAF50;
}

.conformite-section {
  margin-top: 20px;
}

.conformite-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.conformite-item {
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.conformite-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.conformite-title {
  font-weight: bold;
  color: #2c3e50;
}

.conformite-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9em;
  font-weight: 500;
}

.conformite-status.conforme {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.conformite-status.non {
  background-color: #ffebee;
  color: #c62828;
}

.conformite-explanation {
  margin: 0;
  color: #666;
  font-size: 0.95em;
  line-height: 1.4;
}

h4 {
  color: #2c3e50;
  margin: 15px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #eee;
}

.result-box {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 25px;
  margin: 20px 0;
}

.categories-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 15px;
}

.category-item {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  gap: 20px;
}

.category-titles {
  flex: 1;
}

.confidence-badge {
  flex-shrink: 0;
  background-color: #e8f5e9;
  color: #2e7d32;
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 0.9em;
  white-space: nowrap;
}

.subcategory {
  margin: 0;
  color: #666;
  font-size: 0.9em;
}

.category-explanation {
  margin: 0;
  color: #666;
  font-size: 0.95em;
  line-height: 1.4;
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.validity-content {
  padding: 15px;
  border-radius: 8px;
  max-height: none;
  overflow-y: visible;
}

.validity-header {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.confidence-section {
  text-align: center;
}

.confidence-section h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 15px;
}

.confidence-value {
  font-size: 1.5em;
  font-weight: bold;
  color: #2e7d32;
  min-width: 70px;
}

.confidence-bar {
  flex-grow: 1;
  height: 20px;
  background-color: #e8f5e9;
  border-radius: 10px;
  overflow: hidden;
}

.confidence-progress {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

.validity-body {
  padding: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
}

.validity-body :deep(strong) {
  color: #2c3e50;
  font-weight: 600;
}

.validity-body :deep(p) {
  margin: 10px 0;
}

.validity-body :deep(ul),
.validity-body :deep(ol) {
  margin: 10px 0;
  padding-left: 20px;
}

.validity-body :deep(li) {
  margin: 5px 0;
}
</style>