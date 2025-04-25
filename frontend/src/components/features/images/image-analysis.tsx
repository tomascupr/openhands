import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'react-hot-toast';
import { Loader2, Upload, X } from 'lucide-react';

import { UploadImageInput } from './upload-image-input';
import { ImagePreview } from './image-preview';
import { Button } from '#/components/shared/buttons/button';

interface ImageAnalysisProps {
  onAnalysisComplete: (result: string) => void;
}

export function ImageAnalysis({ onAnalysisComplete }: ImageAnalysisProps) {
  const { t } = useTranslation();
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analysisType, setAnalysisType] = useState<string>('describe');
  const [prompt, setPrompt] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  const handleImageUpload = (files: File[]) => {
    if (files.length > 0) {
      const file = files[0];
      setSelectedImage(file);
      
      // Create a preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const clearImage = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedImage(null);
    setPreviewUrl(null);
  };

  const analyzeImage = async () => {
    if (!selectedImage) {
      toast.error(t('Please select an image first'));
      return;
    }

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedImage);
      formData.append('analysis_type', analysisType);
      
      if (prompt) {
        formData.append('prompt', prompt);
      }

      const response = await fetch('/api/images/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const result = await response.json();
      
      // Format the result for display
      const formattedResult = `## Image Analysis: ${result.analysis_type}\n\n${result.content}`;
      
      // Pass the result back to the parent component
      onAnalysisComplete(formattedResult);
      
      // Clear the image after successful analysis
      clearImage();
    } catch (error) {
      console.error('Error analyzing image:', error);
      toast.error(t('Failed to analyze image'));
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
      <h3 className="text-lg font-medium">{t('Image Analysis')}</h3>
      
      {!selectedImage ? (
        <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg border-gray-300 dark:border-gray-600">
          <Upload className="w-12 h-12 mb-2 text-gray-400" />
          <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
            {t('Click to upload or drag and drop')}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {t('PNG, JPG or GIF (MAX. 10MB)')}
          </p>
          <UploadImageInput
            onUpload={handleImageUpload}
            label={
              <Button variant="primary" className="mt-4">
                {t('Select Image')}
              </Button>
            }
          />
        </div>
      ) : (
        <div className="relative">
          <button
            onClick={clearImage}
            className="absolute top-2 right-2 p-1 bg-gray-800 bg-opacity-50 rounded-full text-white hover:bg-opacity-70"
            aria-label={t('Remove image')}
          >
            <X className="w-5 h-5" />
          </button>
          <ImagePreview src={previewUrl!} alt="Selected image" />
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="analysis-type" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">
            {t('Analysis Type')}
          </label>
          <select
            id="analysis-type"
            value={analysisType}
            onChange={(e) => setAnalysisType(e.target.value)}
            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
          >
            <option value="describe">{t('Describe Image')}</option>
            <option value="ocr">{t('Extract Text (OCR)')}</option>
            <option value="code">{t('Analyze Code')}</option>
            <option value="ui">{t('Analyze UI')}</option>
            <option value="diagram">{t('Analyze Diagram')}</option>
          </select>
        </div>
        
        <div>
          <label htmlFor="prompt" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">
            {t('Custom Prompt (Optional)')}
          </label>
          <input
            type="text"
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={t('Enter a custom prompt...')}
            className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
          />
        </div>
      </div>
      
      <Button
        variant="primary"
        onClick={analyzeImage}
        disabled={!selectedImage || isAnalyzing}
        className="mt-2"
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            {t('Analyzing...')}
          </>
        ) : (
          t('Analyze Image')
        )}
      </Button>
    </div>
  );
}