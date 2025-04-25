import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Image } from 'lucide-react';
import { Button } from '#/components/shared/buttons/button';
import { ImageAnalysis } from '../images/image-analysis';
import { Modal } from '#/components/shared/modals/base-modal/modal';

interface ImageAnalysisButtonProps {
  onAnalysisComplete: (result: string) => void;
  disabled?: boolean;
}

export function ImageAnalysisButton({
  onAnalysisComplete,
  disabled = false,
}: ImageAnalysisButtonProps) {
  const { t } = useTranslation();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleAnalysisComplete = (result: string) => {
    onAnalysisComplete(result);
    setIsModalOpen(false);
  };

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsModalOpen(true)}
        disabled={disabled}
        title={t('Analyze Image')}
        aria-label={t('Analyze Image')}
        className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
      >
        <Image className="w-5 h-5" />
      </Button>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={t('Image Analysis')}
        size="lg"
      >
        <ImageAnalysis onAnalysisComplete={handleAnalysisComplete} />
      </Modal>
    </>
  );
}