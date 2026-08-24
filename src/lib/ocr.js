export async function extractTextFromImage(file, onProgress) {
  const { createWorker } = await import('tesseract.js');
  const worker = await createWorker('eng', 1, {
    logger: m => {
      if (m.status === 'recognizing text' && onProgress) onProgress(Math.round((m.progress || 0) * 100));
    },
  });
  try {
    const { data } = await worker.recognize(file);
    return (data.text || '').replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim();
  } catch {
    return '';
  } finally {
    await worker.terminate();
  }
}
