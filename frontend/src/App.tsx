import React, { useState, useEffect } from 'react'
import { 
  Smartphone, 
  Tablet, 
  Monitor, 
  Upload, 
  Download,
  Zap,
  CheckCircle2,
  AlertCircle,
  Settings,
  Palette,
  Globe
} from 'lucide-react'
import axios from 'axios'
import { WebsiteConfig, GenerationStatus, UploadedImage, Template } from './types'

const App = () => {
  const [config, setConfig] = useState<WebsiteConfig>({
    name: 'Мой новый сайт',
    description: 'Современный адаптивный веб-сайт для всех устройств',
    style: 'modern',
    theme: 'light',
    targetDevices: ['mobile', 'tablet', 'desktop'],
    seoEnabled: true,
    multiLanguage: false
  })
  
  const [images, setImages] = useState<UploadedImage[]>([])
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus | null>(null)
  const [templates, setTemplates] = useState<Template[]>([])
  const [isGenerating, setIsGenerating] = useState(false)

  const deviceIcons = {
    mobile: Smartphone,
    tablet: Tablet,
    desktop: Monitor
  }

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      const response = await axios.get('/api/templates')
      setTemplates(response.data)
    } catch (error) {
      console.error('Error loading templates:', error)
    }
  }

  const handleGenerate = async () => {
    if (!config.name.trim() || !config.description.trim()) {
      alert('Пожалуйста, заполните название и описание сайта')
      return
    }

    setIsGenerating(true)
    setGenerationStatus(null)

    try {
      const formData = new FormData()
      formData.append('site_name', config.name)
      formData.append('description', config.description)
      formData.append('style', config.style)
      formData.append('theme', config.theme)
      formData.append('target_devices', JSON.stringify(config.targetDevices))
      formData.append('seo_enabled', config.seoEnabled.toString())
      formData.append('multi_language', config.multiLanguage.toString())
      
      images.forEach(image => {
        if (image.status === 'success') {
          formData.append('images', image.file)
        }
      })

      const response = await axios.post('/api/generate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.data.status === 'processing') {
        const generationId = response.data.generation_id
        await pollGenerationStatus(generationId)
      }
    } catch (error) {
      console.error('Generation error:', error)
      setGenerationStatus({
        generation_id: 'error',
        status: 'error',
        progress: 0,
        message: 'Ошибка при генерации сайта',
        error: error.response?.data?.detail || 'Неизвестная ошибка'
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const pollGenerationStatus = async (generationId: string) => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`/api/generation/${generationId}`)
        const status: GenerationStatus = response.data
        
        setGenerationStatus(status)

        if (status.status === 'processing') {
          setTimeout(checkStatus, 2000)
        }
      } catch (error) {
        console.error('Status check error:', error)
        setGenerationStatus({
          generation_id: generationId,
          status: 'error',
          progress: 0,
          message: 'Ошибка при проверке статуса',
          error: 'Connection error'
        })
      }
    }
    
    await checkStatus()
  }

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    const newImages: UploadedImage[] = files.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      name: file.name,
      status: 'uploading'
    }))
    
    setImages(prev => [...prev, ...newImages])

    // Симуляция загрузки
    newImages.forEach((image, index) => {
      setTimeout(() => {
        setImages(prev => 
          prev.map(img => 
            img.name === image.name 
              ? { ...img, status: 'success' as const }
              : img
          )
        )
      }, 1000 + index * 500)
    })
  }

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index))
  }

  const downloadWebsite = async (format: string = 'zip') => {
    if (!generationStatus?.generation_id) return
    
    try {
      const response = await axios.get(`/api/download/${generationStatus.generation_id}?format=${format}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `website_${generationStatus.generation_id}.${format === 'zip' ? 'zip' : 'html'}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Download error:', error)
    }
  }

  return (
    <div className="min-h-screen bg-fedora-light font-fedora">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <Zap className="h-8 w-8 text-fedora-blue" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Fedora AI Website Generator
                </h1>
                <p className="text-sm text-gray-600">
                  Создавайте адаптивные сайты с искусственным интеллектом
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {generationStatus?.status === 'completed' && (
                <button 
                  onClick={() => downloadWebsite('zip')}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Скачать сайт
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Левая панель - настройки */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Информация о сайте */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Globe className="w-5 h-5 mr-2 text-fedora-blue" />
                Информация о сайте
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Название сайта *
                  </label>
                  <input
                    type="text"
                    value={config.name}
                    onChange={(e) => setConfig({...config, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fedora-blue focus:border-transparent"
                    placeholder="Введите название вашего сайта"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Описание сайта *
                  </label>
                  <textarea
                    value={config.description}
                    onChange={(e) => setConfig({...config, description: e.target.value})}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fedora-blue focus:border-transparent"
                    placeholder="Опишите purpose и особенности вашего сайта"
                  />
                </div>
              </div>
            </div>

            {/* Стиль и тема */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Palette className="w-5 h-5 mr-2 text-fedora-blue" />
                Стиль и оформление
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Стиль дизайна
                  </label>
                  <select
                    value={config.style}
                    onChange={(e) => setConfig({...config, style: e.target.value as any})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fedora-blue focus:border-transparent"
                  >
                    <option value="modern">Современный</option>
                    <option value="classic">Классический</option>
                    <option value="minimal">Минимализм</option>
                    <option value="creative">Креативный</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Цветовая тема
                  </label>
                  <select
                    value={config.theme}
                    onChange={(e) => setConfig({...config, theme: e.target.value as any})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fedora-blue focus:border-transparent"
                  >
                    <option value="light">Светлая</option>
                    <option value="dark">Темная</option>
                    <option value="auto">Авто</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Устройства */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">Целевые устройства</h2>
              <div className="grid grid-cols-3 gap-4">
                {['mobile', 'tablet', 'desktop'].map(device => {
                  const Icon = deviceIcons[device]
                  const isSelected = config.targetDevices.includes(device)
                  
                  return (
                    <div
                      key={device}
                      onClick={() => {
                        const newDevices = isSelected
                          ? config.targetDevices.filter(d => d !== device)
                          : [...config.targetDevices, device]
                        setConfig({...config, targetDevices: newDevices})
                      }}
                      className={`border-2 rounded-lg p-4 text-center cursor-pointer transition-all ${
                        isSelected
                          ? 'border-fedora-blue bg-blue-50 shadow-sm'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <Icon className={`h-8 w-8 mx-auto mb-2 ${
                        isSelected ? 'text-fedora-blue' : 'text-gray-400'
                      }`} />
                      <span className="text-sm font-medium capitalize">
                        {device === 'mobile' ? 'Мобильные' : 
                         device === 'tablet' ? 'Планшеты' : 'Компьютеры'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Дополнительные настройки */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center">
                <Settings className="w-5 h-5 mr-2 text-fedora-blue" />
                Дополнительные настройки
              </h2>
              <div className="space-y-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.seoEnabled}
                    onChange={(e) => setConfig({...config, seoEnabled: e.target.checked})}
                    className="rounded border-gray-300 text-fedora-blue focus:ring-fedora-blue"
                  />
                  <span className="text-sm font-medium text-gray-700">SEO оптимизация</span>
                </label>
                
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={config.multiLanguage}
                    onChange={(e) => setConfig({...config, multiLanguage: e.target.checked})}
                    className="rounded border-gray-300 text-fedora-blue focus:ring-fedora-blue"
                  />
                  <span className="text-sm font-medium text-gray-700">Мультиязычная поддержка</span>
                </label>
              </div>
            </div>

            {/* Изображения */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">Изображения</h2>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">
                  Перетащите изображения или нажмите для загрузки
                </p>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="bg-fedora-blue text-white px-6 py-2 rounded-lg cursor-pointer hover:bg-blue-700 transition-colors inline-block"
                >
                  Выбрать файлы
                </label>
              </div>
              
              {/* Preview изображений */}
              {images.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-lg font-medium mb-3">Загруженные изображения ({images.length})</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {images.map((image, index) => (
                      <div key={index} className="relative group">
                        <img
                          src={image.preview}
                          alt={image.name}
                          className="w-full h-24 object-cover rounded-lg"
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                          <button
                            onClick={() => removeImage(index)}
                            className="text-white bg-red-500 hover:bg-red-600 rounded-full p-1"
                          >
                            <AlertCircle className="w-4 h-4" />
                          </button>
                        </div>
                        <div className="text-xs text-gray-500 truncate mt-1">
                          {image.name}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Кнопка генерации */}
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !config.name.trim() || !config.description.trim()}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-white transition-all ${
                isGenerating || !config.name.trim() || !config.description.trim()
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-fedora-blue hover:bg-blue-700 shadow-lg hover:shadow-xl'
              }`}
            >
              {isGenerating ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                  Генерация сайта...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Сгенерировать сайт
                </div>
              )}
            </button>
          </div>

          {/* Правая панель - превью и статус */}
          <div className="space-y-6">
            
            {/* Статус генерации */}
            {generationStatus && (
              <div className={`rounded-xl shadow-sm border p-6 ${
                generationStatus.status === 'completed' ? 'bg-green-50 border-green-200' :
                generationStatus.status === 'error' ? 'bg-red-50 border-red-200' :
                'bg-blue-50 border-blue-200'
              }`}>
                <div className="flex items-center mb-4">
                  {generationStatus.status === 'completed' && (
                    <CheckCircle2 className="h-6 w-6 text-green-600 mr-2" />
                  )}
                  {generationStatus.status === 'error' && (
                    <AlertCircle className="h-6 w-6 text-red-600 mr-2" />
                  )}
                  {generationStatus.status === 'processing' && (
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
                  )}
                  <h3 className="text-lg font-semibold">
                    {generationStatus.status === 'completed' ? 'Готово!' :
                     generationStatus.status === 'error' ? 'Ошибка' :
                     'Генерация...'}
                  </h3>
                </div>
                
                <div className="space-y-3">
                  <div className="text-sm">
                    <div className="flex justify-between mb-1">
                      <span>Прогресс:</span>
                      <span>{generationStatus.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          generationStatus.status === 'completed' ? 'bg-green-600' :
                          generationStatus.status === 'error' ? 'bg-red-600' :
                          'bg-blue-600'
                        }`}
                        style={{ width: `${generationStatus.progress}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <p className="text-sm">{generationStatus.message}</p>
                  
                  {generationStatus.error && (
                    <p className="text-sm text-red-600">{generationStatus.error}</p>
                  )}
                  
                  {generationStatus.status === 'completed' && generationStatus.result_url && (
                    <div className="space-y-2">
                      <a
                        href={generationStatus.result_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full bg-green-600 text-white text-center py-2 rounded-lg hover:bg-green-700 transition-colors"
                      >
                        Открыть сайт
                      </a>
                      <button
                        onClick={() => downloadWebsite('zip')}
                        className="block w-full border border-green-600 text-green-600 text-center py-2 rounded-lg hover:bg-green-50 transition-colors"
                      >
                        Скачать ZIP
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Превью */}
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">Предпросмотр</h2>
              {generationStatus?.result_url ? (
                <div className="border rounded-lg overflow-hidden">
                  <iframe
                    src={generationStatus.result_url}
                    className="w-full h-96"
                    title="Website Preview"
                  />
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg h-96 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Globe className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p>Превью появится здесь</p>
                    <p className="text-sm">после генерации сайта</p>
                  </div>
                </div>
              )}
            </div>

            {/* Шаблоны */}
            {templates.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-xl font-semibold mb-4">Готовые шаблоны</h2>
                <div className="space-y-3">
                  {templates.slice(0, 3).map(template => (
                    <div
                      key={template.id}
                      className="border rounded-lg p-3 cursor-pointer hover:border-fedora-blue transition-colors"
                      onClick={() => setConfig({
                        ...config,
                        style: template.styles[0] as any,
                        description: template.description
                      })}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center">
                          <Palette className="w-5 h-5 text-gray-500" />
                        </div>
                        <div>
                          <h4 className="font-medium text-sm">{template.name}</h4>
                          <p className="text-xs text-gray-500">{template.category}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App