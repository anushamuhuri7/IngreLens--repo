export async function analyzeIngredients({ text, file, productName, profile }) {
  const formData = new FormData();
  formData.append('product_name', productName || 'Product Analysis');
  formData.append('profile_json', JSON.stringify(profile || {}));

  let endpoint = '/api/scan/text';
  if (file) {
    formData.append('file', file);
    endpoint = '/api/scan/image';
  } else {
    formData.append('text', text);
  }

  const res = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Analysis failed. Please try again.');
  }

  return await res.json();
}