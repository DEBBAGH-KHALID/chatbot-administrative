import React, { useState } from "react";
import {
  Mail,
  Lock,
  User,
  ShieldAlert,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { loginUser, registerUser } from "../services/api";

export default function Login({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nomComplet, setNomComplet] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);

    try {
      if (isRegister) {
        if (!nomComplet.trim() || !email.trim() || !password.trim()) {
          throw new Error("Veuillez remplir tous les champs.");
        }
        await registerUser(email, password, nomComplet);
        setSuccessMsg("Inscription réussie ! Connexion automatique...");
        
        const loginData = await loginUser(email, password);
        
        // 🔑 SAUVEGARDE CRUCIALE DU TOKEN DANS LE LOCALSTORAGE
        if (loginData && loginData.access_token) {
          localStorage.setItem("token", loginData.access_token);
        }
        
        onLoginSuccess(loginData.user);
      } else {
        if (!email.trim() || !password.trim()) {
          throw new Error("Veuillez remplir tous les champs.");
        }
        const loginData = await loginUser(email, password);
        
        // 🔑 SAUVEGARDE CRUCIALE DU TOKEN DANS LE LOCALSTORAGE
        if (loginData && loginData.access_token) {
          localStorage.setItem("token", loginData.access_token);
        }
        
        onLoginSuccess(loginData.user);
      }
    } catch (err) {
      setError(err.message || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-50 text-slate-800 p-4 relative overflow-hidden">
      {/* Halos décoratifs discrets */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-emerald-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md bg-white border border-slate-200/80 rounded-3xl p-8 shadow-xl relative z-10 animate-fadeIn">
        {/* En-tête / Logo */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="mx-auto w-20 h-20 rounded-3xl bg-white border-2 border-slate-200 flex items-center justify-center shadow-md overflow-hidden mb-4 p-1.5">
            <img
              src="/logo_chat.png"
              alt="Logo Portail Administratif"
              className="w-full h-full object-contain scale-[1.6]"
            />
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-700 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Portail Administratif 🇲🇦</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-wide">
            {isRegister ? "Créer un compte" : "Espace Citoyen"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isRegister
              ? "Inscrivez-vous pour conserver et personnaliser vos conversations"
              : "Connectez-vous pour accéder à vos démarches CNIE & Passeport"}
          </p>
        </div>

        {/* Formulaire */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-600 text-xs flex items-start gap-2.5 animate-shake">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
          )}

          {isRegister && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-600 block ml-1">
                Nom complet
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  placeholder="Mohammed Alami"
                  value={nomComplet}
                  onChange={(e) => setNomComplet(e.target.value)}
                  className="w-full bg-slate-50 text-slate-800 placeholder-slate-400 text-sm pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 focus:bg-white transition-all"
                  disabled={loading}
                />
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-600 block ml-1">
              Adresse e-mail
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail className="w-4 h-4" />
              </div>
              <input
                type="email"
                placeholder="citoyen@domaine.ma"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-50 text-slate-800 placeholder-slate-400 text-sm pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 focus:bg-white transition-all"
                disabled={loading}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-600 block ml-1">
              Mot de passe
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-50 text-slate-800 placeholder-slate-400 text-sm pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-600 focus:bg-white transition-all"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 mt-2 px-4 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-all duration-200 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed group shadow-md cursor-pointer"
          >
            {loading ? (
              <span className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white animate-spin" />
            ) : (
              <>
                <span>{isRegister ? "Créer mon compte" : "Se connecter"}</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        {/* Bascule Connexion / Inscription */}
        <div className="mt-8 text-center text-xs text-slate-500">
          {isRegister ? (
            <p>
              Déjà inscrit ?{" "}
              <button
                onClick={() => {
                  setIsRegister(false);
                  setError("");
                }}
                className="text-emerald-700 hover:underline font-semibold focus:outline-none ml-1 cursor-pointer"
                disabled={loading}
              >
                Se connecter
              </button>
            </p>
          ) : (
            <p>
              Nouveau sur la plateforme ?{" "}
              <button
                onClick={() => {
                  setIsRegister(true);
                  setError("");
                }}
                className="text-emerald-700 hover:underline font-semibold focus:outline-none ml-1 cursor-pointer"
                disabled={loading}
              >
                Créer un compte
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}