import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  User,
  Sparkles,
  ChevronRight,
  Menu,
  X,
  Globe,
  Check,
  Copy,
  RefreshCw,
  ShieldCheck,
  CreditCard,
  Heart,
  Car,
  Landmark,
  ThumbsUp,
  ThumbsDown,
  Info,
  LogOut,
} from "lucide-react";

import {
  poserQuestion,
  envoyerMessageVocal,
  getMesConversations,
  getHistoriqueConversation,
  getProfile,
  verifierStatutAPI,
} from "../services/api";
import Login from "./Login";

const STORAGE_KEY_CONV_ID = "morocco_admin_conversation_id";
const API_BASE_URL = "https://chatbot-administrative-et6y.vercel.app";

// 🖼️ Helper pour formater correctement les URLs des images statiques Vercel
const formatImageUrl = (path) => {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;

  // Garantir une barre oblique initiale
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  // Combiner avec l'URL Vercel et encoder proprement les espaces (ex: "la carte bancaire")
  return encodeURI(`${API_BASE_URL}${cleanPath}`);
};

// Helper universel pour récupérer le token JWT
const getStoredToken = () => localStorage.getItem("token") || localStorage.getItem("access_token");

// Suggestions rapides
const QUICK_SUGGESTIONS = [
  {
    id: "cnie",
    title: "Carte d'Identité (CNIE)",
    desc: "Demande, renouvellement ou perte de la CNIE",
    prompt: "Quelles sont les pièces nécessaires pour cree ma carte d'identité nationale (CNIE) au Maroc ?",
    icon: CreditCard,
  },
  {
    id: "passeport",
    title: "Passeport Biométrique",
    desc: "Documents requis & achat du timbre fiscal 300 DH",
    prompt: "Comment demander un passeport biométrique au Maroc et où acheter le timbre fiscal ?",
    icon: ShieldCheck,
  },
  {
    id: "mariage",
    title: "Acte de Mariage",
    desc: "Procédure d'Adoul, pièces requises & dossier de mariage",
    prompt: "Quels sont les documents nécessaires pour établir un acte de mariage au Maroc ?",
    icon: Heart,
  },
  {
    id: "permis",
    title: "Permis de Conduire",
    desc: "Procédure NARSA, duplicata après perte et renouvellement",
    prompt: "Quelle est la procédure pour obtenir permis de conduire ?",
    icon: Car,
  },
  {
    id: "carte_bancaire",
    title: "Services & Carte Bancaire",
    desc: "Ouverture de compte, opposition & demande de carte",
    prompt: "Comment faire opposition sur ma carte bancaire en cas de perte ou de vol ?",
    icon: Landmark,
  },
];

// Messages d'accueil
const WELCOME_MESSAGES = {
  fr: "Bonjour ! \n\nJe suis votre **Assistant Administratif Virtuel**. Comment puis-je vous aider aujourd'hui dans vos démarches pour la **Carte Nationale (CNIE)**, le **Passeport**, le **Permis de Conduire**, le **Mariage** ou votre **Carte Bancaire** ?",
  ar: "السلام عليكم ! \n\nأنا **مساعدك الإداري الافتراضي**. كيف يمكنني مساعدتك اليوم في الإجراءات الخاصة بـ **البطاقة الوطنية (CNIE)**، **جواز السفر**، **رخصة السياقة**، **عقد الزواج** أو **البطاقة البنكية** ؟",
  darija: "السلام ! \n\nأنا **المساعد الإداري الافتراضي** ديالك. كيفاش نقدر نعاونك اليوم ف الإجراءات د **لاكارت ناصيونال (CNIE)**، **الباسبور**، **البيرمي**، **عقد الزواج** ولا **الكارت بنكير** ؟",
};

const getInitialBotMessage = (lang = "fr") => ({
  id: "msg_welcome",
  sender: "assistant",
  text: WELCOME_MESSAGES[lang] || WELCOME_MESSAGES.fr,
  images: [],
  timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
});

export default function ChatApp() {
  const [token, setToken] = useState(getStoredToken());
  const [currentUser, setCurrentUser] = useState(null);

  // State management
  const [currentLang, setCurrentLang] = useState("fr");
  const [messages, setMessages] = useState([getInitialBotMessage("fr")]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [history, setHistory] = useState([]);
  const [historySearch, setHistorySearch] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [apiOnline, setApiOnline] = useState(true);
  const [currentlySpeakingId, setCurrentlySpeakingId] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Voice Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingTimerRef = useRef(null);

  // DOM Refs
  const chatBottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    const activeToken = getStoredToken();
    if (activeToken) {
      checkApiHealth();
      getProfile()
        .then((user) => setCurrentUser(user))
        .catch((err) => console.error("Failed to load user profile:", err));

      fetchHistoryList();

      const savedConvId = localStorage.getItem(STORAGE_KEY_CONV_ID);
      if (savedConvId) {
        setConversationId(savedConvId);
        loadSpecificConversation(savedConvId);
      }
    }
  }, [token]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const checkApiHealth = async () => {
    const online = await verifierStatutAPI();
    setApiOnline(online);
  };

  const fetchHistoryList = async () => {
    try {
      const data = await getMesConversations();
      if (Array.isArray(data)) {
        setHistory(data);
      }
    } catch (err) {
      console.warn("Could not retrieve conversation list from API:", err);
    }
  };

  const loadSpecificConversation = async (id) => {
    if (!id) return;
    setIsLoading(true);
    try {
      const data = await getHistoriqueConversation(id);
      if (Array.isArray(data) && data.length > 0) {
        const mapped = [];
        data.forEach((exchange, idx) => {
          const time = exchange.created_at
            ? new Date(exchange.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            : "";
          mapped.push({
            id: `msg_user_${idx}_${Date.now()}`,
            sender: "user",
            text: exchange.question,
            timestamp: time,
          });
          mapped.push({
            id: `msg_bot_${idx}_${Date.now()}`,
            sender: "assistant",
            text: exchange.reponse,
            images: Array.isArray(exchange.images) ? exchange.images : [],
            timestamp: time,
          });
        });
        setMessages(mapped);
        setConversationId(id);
        localStorage.setItem(STORAGE_KEY_CONV_ID, id);
      } else {
        setMessages([getInitialBotMessage(currentLang)]);
      }
    } catch (err) {
      console.warn("Failed to load specific conversation history:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLanguageChange = (lang) => {
    setCurrentLang(lang);
    if (messages.length === 1 && (messages[0].id === "msg_welcome" || messages[0].sender === "assistant")) {
      setMessages([getInitialBotMessage(lang)]);
    }
  };

  const speakNative = (msgId, text) => {
    if (!("speechSynthesis" in window)) {
      alert("La synthèse vocale n'est pas supportée par votre navigateur.");
      return;
    }

    if (currentlySpeakingId === msgId) {
      window.speechSynthesis.cancel();
      setCurrentlySpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();
    const textPropre = text.replace(/[*#`_~]/g, "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
    const utterance = new SpeechSynthesisUtterance(textPropre);

    const assignVoice = () => {
      const voices = window.speechSynthesis.getVoices();
      const targetLang = currentLang === "ar" || currentLang === "darija" ? "ar" : "fr";
      const bestVoice =
        voices.find((v) => v.lang.includes(targetLang) && (v.name.includes("Google") || v.name.includes("Natural"))) ||
        voices.find((v) => v.lang.includes(targetLang)) ||
        voices[0];

      if (bestVoice) utterance.voice = bestVoice;
      utterance.rate = 0.95;
      utterance.onend = () => setCurrentlySpeakingId(null);
      utterance.onerror = () => setCurrentlySpeakingId(null);

      setCurrentlySpeakingId(msgId);
      window.speechSynthesis.speak(utterance);
    };

    if (window.speechSynthesis.getVoices().length > 0) {
      assignVoice();
    } else {
      window.speechSynthesis.onvoiceschanged = assignVoice;
    }
  };

  const handleNewDiscussion = () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    setCurrentlySpeakingId(null);
    setMessages([getInitialBotMessage(currentLang)]);
    setConversationId(null);
    localStorage.removeItem(STORAGE_KEY_CONV_ID);
  };

  const handleLogout = () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    localStorage.removeItem(STORAGE_KEY_CONV_ID);
    setToken(null);
    setCurrentUser(null);
    setMessages([getInitialBotMessage("fr")]);
    setConversationId(null);
    setHistory([]);
  };

  const handleInputTextChange = (e) => {
    setInputText(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  };

  const handleSendText = async (customPrompt = null) => {
    const textToSend = customPrompt || inputText;
    if (!textToSend.trim() || isLoading) return;

    const userMsgId = "msg_user_" + Date.now();
    const userMessage = {
      id: userMsgId,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!customPrompt) setInputText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsLoading(true);

    try {
      const data = await poserQuestion(textToSend, conversationId, currentLang);
      const botMessage = {
        id: "msg_bot_" + Date.now(),
        sender: "assistant",
        text: data.reponse || "Désolé, une erreur serveur est survenue lors de la recherche.",
        images: Array.isArray(data.images) ? data.images : [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        localStorage.setItem(STORAGE_KEY_CONV_ID, data.conversation_id);
      }

      setMessages((prev) => [...prev, botMessage]);
      setApiOnline(true);
      fetchHistoryList();
    } catch (err) {
      console.warn("API call failed:", err);
      setApiOnline(false);

      setTimeout(() => {
        const botMessage = {
          id: "msg_bot_" + Date.now(),
          sender: "assistant",
          text:
            currentLang === "darija"
              ? "Erreur de connexion. Veuillez vérifier le serveur."
              : "Impossible de contacter l'assistant. Veuillez vérifier votre connexion au serveur.",
          images: [],
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, botMessage]);
        setIsLoading(false);
      }, 700);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
      clearInterval(recordingTimerRef.current);
      setRecordingSeconds(0);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? { mimeType: "audio/webm;codecs=opus", audioBitsPerSecond: 32000 }
          : { audioBitsPerSecond: 32000 };

        const mediaRecorder = new MediaRecorder(stream, options);

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          stream.getTracks().forEach((track) => track.stop());
          await sendVocalToApi(audioBlob);
        };

        mediaRecorder.start();
        mediaRecorderRef.current = mediaRecorder;
        setIsRecording(true);
        setRecordingSeconds(0);

        recordingTimerRef.current = setInterval(() => {
          setRecordingSeconds((prev) => prev + 1);
        }, 1000);
      } catch (err) {
        alert("Impossible d'accéder au microphone. Veuillez autoriser l'accès dans votre navigateur.");
        console.error("Microphone error:", err);
      }
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.onstop = null;
      if (mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      }
    }
    clearInterval(recordingTimerRef.current);
    audioChunksRef.current = [];
    setIsRecording(false);
    setRecordingSeconds(0);
  };

  const sendVocalToApi = async (audioBlob) => {
    const tempUserMsgId = "msg_user_" + Date.now();
    const placeholderMsg = {
      id: tempUserMsgId,
      sender: "user",
      text: "🎤 Message vocal (en cours de transcription...)",
      isVocal: true,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, placeholderMsg]);
    setIsLoading(true);

    try {
      const data = await envoyerMessageVocal(audioBlob, conversationId, currentLang);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempUserMsgId
            ? { ...msg, text: `🎤 "${data.question_transcrite || "Vocal transcrit"}"` }
            : msg
        )
      );

      const botMessage = {
        id: "msg_bot_" + Date.now(),
        sender: "assistant",
        text: data.reponse || "Réponse vocale générée.",
        images: data.images || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        localStorage.setItem(STORAGE_KEY_CONV_ID, data.conversation_id);
      }

      setMessages((prev) => [...prev, botMessage]);
      setApiOnline(true);
      fetchHistoryList();
    } catch (err) {
      console.warn("Vocal API failed:", err);
      setApiOnline(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyText = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDeleteHistoryItem = (e, histId) => {
    e.stopPropagation();
    const updated = history.filter((item) => (item.conversation_id || item.id) !== histId);
    setHistory(updated);
    if (conversationId === histId) {
      handleNewDiscussion();
    }
  };

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const renderFormattedText = (content) => {
    if (!content) return null;
    const lines = content.split("\n");
    return lines.map((line, idx) => {
      let trimmed = line.trim();
      if (trimmed.startsWith("### ")) {
        return <h3 key={idx} className="text-base font-semibold text-slate-800 mt-3 mb-1">{trimmed.replace("### ", "")}</h3>;
      }
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        return <li key={idx} className="ml-4 list-disc text-slate-700 my-0.5">{parseBoldText(trimmed.substring(2))}</li>;
      }
      if (/^\d+\.\s/.test(trimmed)) {
        return <div key={idx} className="ml-2 font-medium text-slate-800 my-1">{parseBoldText(trimmed)}</div>;
      }
      if (!trimmed) {
        return <div key={idx} className="h-2" />;
      }
      return <p key={idx} className="text-slate-700 leading-relaxed my-1">{parseBoldText(trimmed)}</p>;
    });
  };

  const parseBoldText = (str) => {
    const parts = str.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  if (!token) {
    return (
      <Login
        onLoginSuccess={(user) => {
          setToken(getStoredToken());
          setCurrentUser(user);
        }}
      />
    );
  }

  const filteredHistory = history.filter((item) =>
    (item.titre || item.question || item.conversation_id || "").toLowerCase().includes(historySearch.toLowerCase())
  );

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-800 font-sans overflow-hidden">
      {sidebarOpen && <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* SIDEBAR */}
      <aside className={`fixed lg:static top-0 bottom-0 left-0 z-50 w-72 bg-slate-900 text-slate-100 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:-ml-72"}`}>
        <div className="p-4 border-b border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-white border border-slate-700 flex items-center justify-center shadow-sm overflow-hidden p-1">
                <img src="/logo-yanecode.png" alt="YaneCode Digital Logo" className="w-full h-full object-contain" />
              </div>
              <span className="font-bold text-sm tracking-wide text-white">YaneCode Digital</span>
            </div>
            <button onClick={() => setSidebarOpen(false)} className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800" title="Fermer la barre latérale">
              <X className="w-5 h-5" />
            </button>
          </div>

          <button onClick={handleNewDiscussion} className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-white font-medium text-sm transition-all duration-200 group cursor-pointer shadow-sm">
            <span className="flex items-center gap-2.5">
              <Plus className="w-4 h-4 text-white group-hover:rotate-90 transition-transform duration-300" />
              Nouvelle discussion
            </span>
            <kbd className="hidden sm:inline-block text-[10px] bg-emerald-800 text-emerald-100 px-1.5 py-0.5 rounded border border-emerald-600">New</kbd>
          </button>
        </div>

        {/* Historique */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5 custom-scrollbar">
          <input
            type="text"
            placeholder="Rechercher une discussion..."
            value={historySearch}
            onChange={(e) => setHistorySearch(e.target.value)}
            className="w-full bg-slate-950 text-slate-200 text-xs px-3 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-emerald-500 mb-2"
          />

          <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Historique</span>
            <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded-full text-slate-300 border border-slate-700">{filteredHistory.length}</span>
          </div>

          {filteredHistory.length === 0 ? (
            <div className="py-8 text-center px-4">
              <MessageSquare className="w-8 h-8 mx-auto text-slate-600 mb-2 stroke-1" />
              <p className="text-xs text-slate-400">Aucune discussion enregistrée</p>
            </div>
          ) : (
            filteredHistory.map((item) => {
              const itemConvId = item.conversation_id || item.id;
              const isActive = conversationId === itemConvId;
              return (
                <div
                  key={itemConvId}
                  onClick={() => loadSpecificConversation(itemConvId)}
                  className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer text-sm transition-all duration-200 ${
                    isActive ? "bg-emerald-950/80 text-emerald-100 font-medium border border-emerald-600/60 shadow-sm" : "text-slate-300 hover:bg-slate-800 hover:text-white border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-2">
                    <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                    <span className="truncate">{item.titre || item.question || `Discussion #${String(itemConvId).slice(-4)}`}</span>
                  </div>

                  <button type="button" onClick={(e) => handleDeleteHistoryItem(e, itemConvId)} className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-400 rounded hover:bg-slate-700 transition-opacity" title="Supprimer">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Sidebar */}
        <div className="p-3 border-t border-slate-800 bg-slate-900 flex flex-col gap-2.5">
          <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <span className="text-slate-400 flex items-center gap-1.5"><Globe className="w-3.5 h-3.5 text-slate-400" /> FastAPI Status:</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${apiOnline ? "bg-emerald-400 animate-pulse" : "bg-red-500"}`} />
              <span className={`font-medium text-[11px] ${apiOnline ? "text-slate-200" : "text-red-400"}`}>{apiOnline ? "Connecté" : "Hors ligne"}</span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 px-2 py-1.5">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-full bg-slate-800 border border-emerald-600/60 flex items-center justify-center text-emerald-400 font-bold text-sm shrink-0">
                {currentUser?.nom_complet ? currentUser.nom_complet.charAt(0).toUpperCase() : "🇲🇦"}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-white truncate">{currentUser?.nom_complet || "Citoyen Marocain"}</span>
                <span className="text-[10px] text-slate-400 truncate">{currentUser?.email || "Espace Citoyen"}</span>
              </div>
            </div>

            <button onClick={handleLogout} title="Déconnexion" className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer shrink-0">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CHAT */}
      <main className="flex-1 flex flex-col h-full bg-white relative overflow-hidden transition-all duration-300">
        <header className="h-16 border-b border-slate-200 bg-white/90 backdrop-blur-md px-4 flex items-center justify-between z-10 shrink-0 shadow-xs">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button onClick={() => setSidebarOpen(true)} className="p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer" title="Ouvrir la barre latérale">
                <Menu className="w-5 h-5" />
              </button>
            )}

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center shadow-xs overflow-hidden shrink-0">
                <img src="/logo_chat.png" alt="Assistant Logo" className="w-full h-full object-contain scale-[1.3]" />
              </div>
              <div>
                <h1 className="font-bold text-base text-slate-900 tracking-wide flex items-center gap-2">Assistant Administratif Marocain <span className="text-sm">🇲🇦</span></h1>
                <p className="text-[11px] text-slate-500 hidden sm:block">Service public & Procédure administrative en ligne</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center bg-slate-100 rounded-xl p-1 border border-slate-200">
              <button type="button" onClick={() => handleLanguageChange("fr")} className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer ${currentLang === "fr" ? "bg-emerald-600 text-white shadow-xs" : "text-slate-600 hover:text-slate-900"}`}>FR</button>
              <button type="button" onClick={() => handleLanguageChange("ar")} className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer ${currentLang === "ar" ? "bg-emerald-600 text-white shadow-xs" : "text-slate-600 hover:text-slate-900"}`}>العربية</button>
              <button type="button" onClick={() => handleLanguageChange("darija")} className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer ${currentLang === "darija" ? "bg-emerald-600 text-white shadow-xs" : "text-slate-600 hover:text-slate-900"}`}>الدارجة</button>
            </div>

            <button onClick={handleNewDiscussion} title="Réinitialiser" className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-transparent cursor-pointer">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Zone de discussion */}
        <div className="flex-1 overflow-y-auto px-4 py-6 custom-scrollbar bg-slate-50/50">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length <= 1 && (
              <div className="py-4 flex flex-col items-center text-center space-y-6 animate-fadeIn">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium shadow-xs">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Assistant Officiel Virtuel</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
                  {QUICK_SUGGESTIONS.map((card) => {
                    const CardIcon = card.icon;
                    return (
                      <div key={card.id} onClick={() => handleSendText(card.prompt)} className="p-4 rounded-2xl bg-white hover:bg-emerald-50/60 border border-slate-200 hover:border-emerald-300 cursor-pointer transition-all duration-200 group shadow-xs hover:shadow-md flex flex-col justify-between">
                        <div className="flex items-start justify-between mb-3">
                          <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                            <CardIcon className="w-5 h-5" />
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-800 text-sm group-hover:text-emerald-900 transition-colors">{card.title}</h3>
                          <p className="text-xs text-slate-500 mt-1 line-clamp-2">{card.desc}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-500 pt-2">
                  <Info className="w-4 h-4 text-emerald-600" />
                  <span>Réponses basées sur les portails officiels du Royaume du Maroc</span>
                </div>
              </div>
            )}

            {/* Messages */}
            {messages.map((msg) => {
              const isUser = msg.sender === "user";
              const isSpeaking = currentlySpeakingId === msg.id;

              return (
                <div key={msg.id} className={`flex gap-3 sm:gap-4 ${isUser ? "justify-end" : "justify-start"} animate-fadeIn`}>
                  {!isUser && (
                    <div className="w-9 h-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-xs mt-1 overflow-hidden">
                      <img src="/logo_chat.png" alt="Bot" className="w-full h-full object-contain scale-[1.4]" />
                    </div>
                  )}

                  <div className={`max-w-[85%] sm:max-w-[80%] rounded-2xl p-4 shadow-xs ${isUser ? "bg-emerald-600 text-white font-medium rounded-tr-none shadow-emerald-600/10" : "bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-xs"}`}>
                    {!isUser && (
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                        <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Assistant Maroc</span>
                        <span className="text-[10px] text-slate-400">{msg.timestamp}</span>
                      </div>
                    )}

                    <div className="text-sm leading-relaxed">
                      {isUser ? <p className="whitespace-pre-wrap">{msg.text}</p> : renderFormattedText(msg.text)}
                    </div>

                    {/* 🖼️ RENDU CORRIGÉ DES IMAGES STATIQUES */}
                    {!isUser && msg.images && msg.images.length > 0 && (
                      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {msg.images.map((imgPath, i) => {
                          const fullImgUrl = formatImageUrl(imgPath);
                          return (
                            <div 
                              key={i} 
                              className="relative group rounded-xl overflow-hidden border border-slate-200 bg-slate-100 p-1.5 flex items-center justify-center cursor-pointer hover:border-emerald-500 transition-all" 
                              onClick={() => window.open(fullImgUrl, "_blank")} 
                              title="Cliquer pour agrandir"
                            >
                              <img 
                                src={fullImgUrl} 
                                alt="Illustration administrative" 
                                className="w-full max-h-52 object-contain rounded-lg group-hover:scale-102 transition-transform duration-300" 
                              />
                              <div className="absolute inset-0 bg-slate-900/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-xs text-white font-medium backdrop-blur-[2px]">
                                🔍 Agrandir l'image
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {!isUser && (
                      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-slate-500 text-xs">
                        <button type="button" onClick={() => speakNative(msg.id, msg.text)} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${isSpeaking ? "bg-emerald-600 text-white font-semibold animate-pulse shadow-xs" : "bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200"}`}>
                          {isSpeaking ? <><VolumeX className="w-3.5 h-3.5 text-white" /><span>Arrêter</span></> : <><Volume2 className="w-3.5 h-3.5 text-emerald-600" /><span>Écouter 🔊</span></>}
                        </button>

                        <div className="flex items-center gap-1">
                          <button onClick={() => handleCopyText(msg.id, msg.text)} className="p-1.5 hover:text-slate-800 hover:bg-slate-100 rounded-md transition-colors cursor-pointer" title="Copier">
                            {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          </button>
                          <button className="p-1.5 hover:text-emerald-600 hover:bg-slate-100 rounded-md transition-colors cursor-pointer" title="Utile"><ThumbsUp className="w-3.5 h-3.5" /></button>
                          <button className="p-1.5 hover:text-red-500 hover:bg-slate-100 rounded-md transition-colors cursor-pointer" title="Pas utile"><ThumbsDown className="w-3.5 h-3.5" /></button>
                        </div>
                      </div>
                    )}

                    {isUser && <div className="text-[10px] text-emerald-100/80 text-right mt-1.5">{msg.timestamp}</div>}
                  </div>

                  {isUser && (
                    <div className="w-9 h-9 rounded-xl bg-slate-200 border border-slate-300 flex items-center justify-center shrink-0 mt-1">
                      <User className="w-5 h-5 text-slate-600" />
                    </div>
                  )}
                </div>
              );
            })}

            {isLoading && (
              <div className="flex gap-3 items-center animate-fadeIn">
                <div className="w-9 h-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center overflow-hidden shadow-xs">
                  <img src="/logo_chat.png" alt="Loading Bot" className="w-full h-full object-contain scale-[2.2] animate-pulse" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-slate-500 text-xs flex items-center gap-2 shadow-xs">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:0.4s]" />
                  </div>
                  <span>Génération de la réponse en cours...</span>
                </div>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>
        </div>

        {/* Footer Input */}
        <footer className="p-4 border-t border-slate-200 bg-white shrink-0">
          <div className="max-w-3xl mx-auto">
            {isRecording && (
              <div className="mb-3 px-4 py-2.5 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between animate-fadeIn">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-red-500 animate-ping" />
                  <span className="text-xs font-semibold text-red-700">Enregistrement vocal en cours...</span>
                  <span className="text-xs font-mono bg-red-100 text-red-800 px-2 py-0.5 rounded border border-red-200">{formatTimer(recordingSeconds)}</span>
                </div>
                <button onClick={cancelRecording} type="button" className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-red-600 hover:text-red-800 bg-white hover:bg-red-100 border border-red-300 rounded-lg transition-all cursor-pointer shadow-xs">
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Annuler</span>
                </button>
              </div>
            )}

            <div className="relative flex items-end gap-2 bg-slate-50 rounded-2xl border border-slate-300 focus-within:border-emerald-600 focus-within:ring-1 focus-within:ring-emerald-600 focus-within:bg-white transition-all p-2 shadow-sm">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={handleInputTextChange}
                onKeyDown={handleKeyDown}
                placeholder={currentLang === "ar" ? "اطرح سؤالك حول الإجراءات الإدارية في المغرب..." : currentLang === "darija" ? "سول على الإجراءات الإدارية ف المغرب..." : "Posez votre question sur les procédures administratives au Maroc..."}
                rows={1}
                className="w-full bg-transparent text-slate-800 placeholder-slate-400 text-sm px-3 py-2 focus:outline-none resize-none max-h-40 custom-scrollbar"
              />

              <div className="flex items-center gap-1.5 shrink-0 pb-1">
                <button onClick={toggleRecording} type="button" title={isRecording ? "Arrêter l'enregistrement" : "Enregistrer un vocal"} className={`p-2.5 rounded-xl transition-all duration-200 cursor-pointer ${isRecording ? "bg-red-600 text-white animate-pulse-ring shadow-md" : "bg-slate-200 hover:bg-slate-300 text-slate-700"}`}>
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>

                <button onClick={() => handleSendText()} disabled={!inputText.trim() || isLoading} type="button" className={`p-2.5 rounded-xl transition-all duration-200 ${inputText.trim() && !isLoading ? "bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-md cursor-pointer" : "bg-slate-200 text-slate-400 cursor-not-allowed"}`}>
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            <p className="text-[10px] text-center text-slate-400 mt-2">Ce chat peut produire des erreurs. Vérifiez les informations auprès des administrations compétentes.</p>
          </div>
        </footer>
      </main>
    </div>
  );
}