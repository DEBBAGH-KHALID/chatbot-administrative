export const API_BASE_URL = 'https://chatbot-administrative-et6y.vercel.app';

function getAuthHeader() {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function request(endpoint, options = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${cleanEndpoint}`;

  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');
    }
    throw new Error(`Erreur HTTP: ${response.status}`);
  }

  return await response.json();
}

// --------------------------------------------------
// EXPORTS D'AUTHENTIFICATION & CHAT
// --------------------------------------------------

export async function loginUser(email, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function registerUser(email, password, nomComplet) {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, nom_complet: nomComplet }),
  });
}

export async function getProfile() {
  return request('/auth/me');
}

//poserQuestion au lieu de envoyerMessageTexte
export async function poserQuestion(text, conversationId, langue) {
  return request('/chat/', {
    method: 'POST',
    body: JSON.stringify({
      question: text,
      conversation_id: conversationId || null,
      langue: langue || 'fr',
    }),
  });
}

export async function envoyerMessageVocal(audioBlob, conversationId, langue) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'enregistrement.webm');
  
  if (conversationId) formData.append('conversation_id', conversationId);
  if (langue) formData.append('langue', langue);

  const response = await fetch(`${API_BASE_URL}/chat/vocal`, {
    method: 'POST',
    headers: { ...getAuthHeader() },
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Erreur serveur vocal (${response.status})`);
  }

  return await response.json();
}

export async function getMesConversations() {
  return request('/chat/mes-conversations');
}

export async function getHistoriqueConversation(conversationId) {
  return request(`/chat/historique/${conversationId}`);
}

export async function verifierStatutAPI() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}