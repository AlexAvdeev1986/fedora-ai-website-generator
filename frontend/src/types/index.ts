export interface WebsiteConfig {
  name: string;
  description: string;
  style: 'modern' | 'classic' | 'minimal' | 'creative';
  theme: 'light' | 'dark' | 'auto';
  targetDevices: string[];
  seoEnabled: boolean;
  multiLanguage: boolean;
}

export interface GenerationStatus {
  generation_id: string;
  status: 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  result_url?: string;
  error?: string;
}

export interface UploadedImage {
  file: File;
  preview: string;
  name: string;
  status: 'uploading' | 'success' | 'error';
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  preview: string;
  styles: string[];
}