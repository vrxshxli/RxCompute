import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Globe2 } from 'lucide-react';

const VoiceAgent = () => {
  const [active, setActive] = useState(false);
  const [recognizing, setRecognizing] = useState(false);
  const [language, setLanguage] = useState(null); // 'en-IN' | 'hi-IN' | 'mr-IN'
  const [transcript, setTranscript] = useState('');
  const [reply, setReply] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectingLanguage, setSelectingLanguage] = useState(false);
  const recRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis || null);
  const [voices, setVoices] = useState([]);
  const welcomeSpokenRef = useRef(false);
  const languageSelectionRef = useRef(false);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

  // Check if language is already selected (from localStorage)
  useEffect(() => {
    const savedLanguage = localStorage.getItem('rxcompute_language');
    if (savedLanguage) {
      setLanguage(savedLanguage);
      languageSelectionRef.current = true; // Don't ask again
    }
  }, []);

  // Auto-start voice agent when component loads
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!active && !language) {
        handleStart();
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Load TTS voices and start language selection
  useEffect(() => {
    if (!synthRef.current) return;
    
    const loadVoices = () => {
      const availableVoices = synthRef.current.getVoices();
      setVoices(availableVoices);
      
      // Only start language selection if not already selected
      const savedLanguage = localStorage.getItem('rxcompute_language');
      if (!savedLanguage && availableVoices.length > 0 && active && !language && !languageSelectionRef.current) {
        startLanguageSelection();
      }
      
      // If language is selected, fetch welcome
      if (availableVoices.length > 0 && language && !welcomeSpokenRef.current) {
        fetchAndSpeakWelcome(language);
      }
    };
    
    synthRef.current.onvoiceschanged = loadVoices;
    loadVoices();
  }, [active, language]);

  // Find best Indian voice
  const pickVoice = (lang) => {
    if (!voices.length) return null;
    
    // Priority: Indian voices first - more specific matching
    const indianVoices = voices.filter(v => {
      const vLang = (v.lang || '').toLowerCase();
      const vName = (v.name || '').toLowerCase();
      return vLang.includes('in') || 
             vLang === lang.toLowerCase() ||
             vName.includes('india') ||
             vName.includes('indian') ||
             vName.includes('hindi') ||
             vName.includes('marathi') ||
             vName.includes('bengali') ||
             vName.includes('telugu') ||
             vName.includes('tamil') ||
             vName.includes('gujarati');
    });
    
    if (indianVoices.length > 0) {
      // Try exact language match first
      let v = indianVoices.find(v => v.lang === lang);
      if (v) return v;
      
      // Try base language match
      const base = (lang || 'en-IN').split('-')[0];
      v = indianVoices.find(v => {
        const vLang = (v.lang || '').toLowerCase();
        return vLang.startsWith(base);
      });
      if (v) return v;
      
      // For Marathi, try to find Marathi-specific voice
      if (lang === 'mr-IN') {
        v = indianVoices.find(v => {
          const vName = (v.name || '').toLowerCase();
          return vName.includes('marathi') || vName.includes('marathi');
        });
        if (v) return v;
      }
      
      // For Hindi, try to find Hindi-specific voice
      if (lang === 'hi-IN') {
        v = indianVoices.find(v => {
          const vName = (v.name || '').toLowerCase();
          return vName.includes('hindi') || vName.includes('hindi');
        });
        if (v) return v;
      }
      
      // Return first Indian voice
      return indianVoices[0];
    }
    
    // Fallback to any voice matching language
    let v = voices.find(v => v.lang === lang);
    if (v) return v;
    const base = (lang || 'en-IN').split('-')[0];
    v = voices.find(v => (v.lang || '').toLowerCase().startsWith(base));
    return v || voices[0];
  };

  // Preprocess text for better pronunciation
  const preprocessText = (text, lang) => {
    // Fix Rxcompute pronunciation
    let processed = text.replace(/Rxcompute/gi, 'R X compute');
    processed = processed.replace(/Rx compute/gi, 'R X compute');
    
    // Add pauses for better natural speech
    processed = processed.replace(/\./g, '. ');
    processed = processed.replace(/\?/g, '? ');
    processed = processed.replace(/!/g, '! ');
    
    return processed;
  };

  const speak = (text, lang) => {
    if (!synthRef.current || !text) return;
    
    // Preprocess text for better pronunciation
    const processedText = preprocessText(text, lang);
    
    const u = new SpeechSynthesisUtterance(processedText);
    const v = pickVoice(lang);
    if (v) {
      u.voice = v;
      console.log('Using voice:', v.name, v.lang);
    }
    u.lang = lang || 'en-IN';
    
    // Optimize for Indian voices - slightly slower and natural pitch
    u.rate = lang === 'hi-IN' || lang === 'mr-IN' ? 0.8 : 0.85;
    u.pitch = 1.0;
    u.volume = 1;
    
    // Wait for current speech to finish
    synthRef.current.cancel();
    
    // Use onend to prevent glitches
    u.onend = () => {
      console.log('Speech ended');
    };
    
    u.onerror = (e) => {
      console.error('Speech error:', e);
    };
    
    synthRef.current.speak(u);
  };

  const startLanguageSelection = async () => {
    if (languageSelectionRef.current) return;
    languageSelectionRef.current = true;
    setSelectingLanguage(true);
    
    try {
      // Get language selection prompts
      const res = await fetch(`${API_BASE}/ai/language-prompt`);
      if (res.ok) {
        const data = await res.json();
        const prompts = data.prompts || {};
        
        // Speak all prompts to let user know options
        const englishPrompt = prompts["en-IN"] || "Hello! I am Rxcompute. Please select your preferred language. Say English, Hindi, or Marathi.";
        speak(englishPrompt, "en-IN");
        
        // Start listening for language selection
        setTimeout(() => {
          startRecognitionForLanguage();
        }, 3000);
      }
    } catch (e) {
      console.error('Error fetching language prompt:', e);
      // Fallback
      speak("Hello! I am Rxcompute. Please select your preferred language. Say English, Hindi, or Marathi.", "en-IN");
      setTimeout(() => {
        startRecognitionForLanguage();
      }, 3000);
    }
  };

  const startRecognitionForLanguage = async () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert('Speech Recognition not supported. Please use Chrome.');
      return;
    }
    
    // Request microphone permission first
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      console.error('Microphone permission denied:', e);
      alert('Please allow microphone access to use voice assistant.');
      return;
    }
    
    stopRecognition();
    
    const rec = new SR();
    rec.lang = 'en-IN'; // Start with English for language selection
    rec.continuous = true;
    rec.interimResults = true; // Show interim results
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      console.log('Language selection recognition started');
      setRecognizing(true);
      setReply("Listening for your language choice...");
    };
    
    rec.onerror = (e) => {
      console.error('Recognition error:', e.error, e);
      setRecognizing(false);
      
      if (e.error === 'no-speech') {
        // No speech detected, restart listening
        if (selectingLanguage && !language) {
          setTimeout(() => startRecognitionForLanguage(), 1000);
        }
      } else if (e.error === 'audio-capture') {
        setReply('Microphone not found. Please check your microphone.');
      } else if (e.error === 'not-allowed') {
        setReply('Microphone permission denied. Please allow microphone access.');
      } else {
        // For other errors, try to restart
        if (selectingLanguage && !language) {
          setTimeout(() => startRecognitionForLanguage(), 2000);
        }
      }
    };
    
    rec.onend = () => {
      console.log('Language selection recognition ended');
      setRecognizing(false);
      if (selectingLanguage && !language) {
        setTimeout(() => startRecognitionForLanguage(), 500);
      }
    };
    
    rec.onresult = (e) => {
      console.log('Language selection result:', e.results.length);
      
      let finalTranscript = '';
      let interimTranscript = '';
      
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const transcript = e.results[i][0].transcript;
        if (e.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      
      // Show interim results
      if (interimTranscript) {
        setTranscript(interimTranscript);
      }
      
      // Process final results
      if (finalTranscript) {
        const text = finalTranscript.trim().toLowerCase();
        console.log('Language selection transcript:', text);
        
        if (!text) return;
        
        setTranscript(text);
        
        // Detect language from user input
        let selectedLang = null;
        if (text.includes('english') || text.includes('angrezi') || text.includes('इंग्रजी') || text.includes('inglish')) {
          selectedLang = 'en-IN';
        } else if (text.includes('hindi') || text.includes('हिंदी') || text.includes('हिन्दी') || text.includes('hindee')) {
          selectedLang = 'hi-IN';
        } else if (text.includes('marathi') || text.includes('मराठी') || text.includes('maratee')) {
          selectedLang = 'mr-IN';
        }
        
        if (selectedLang) {
          console.log('Language selected:', selectedLang);
          rec.stop();
          setSelectingLanguage(false);
          setLanguage(selectedLang);
          // Save to localStorage so it doesn't ask again
          localStorage.setItem('rxcompute_language', selectedLang);
          languageSelectionRef.current = true; // Mark as done
          welcomeSpokenRef.current = false;
          setTimeout(() => {
            fetchAndSpeakWelcome(selectedLang);
          }, 500);
        } else {
          // Ask again
          const retryMsg = "I didn't understand. Please say English, Hindi, or Marathi.";
          speak(retryMsg, "en-IN");
          setReply(retryMsg);
        }
      }
    };

    recRef.current = rec;
    try {
      console.log('Starting language selection recognition');
      rec.start();
    } catch (e) {
      console.error('Error starting recognition:', e);
      setReply('Error starting voice recognition. Please try again.');
    }
  };

  const fetchAndSpeakWelcome = async (lang) => {
    if (welcomeSpokenRef.current) return;
    
    try {
      setIsLoading(true);
      const res = await fetch(`${API_BASE}/ai/welcome`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: lang })
      });
      
      if (res.ok) {
        const data = await res.json();
        const welcomeMsg = data.message || '';
        if (welcomeMsg) {
          setReply(welcomeMsg);
          speak(welcomeMsg, lang);
          welcomeSpokenRef.current = true;
          
          setTimeout(() => {
            startRecognition(lang);
          }, 2000);
        }
      }
    } catch (e) {
      console.error('Error fetching welcome message:', e);
      const fallbackMsg = 
        lang === 'hi-IN' ? 'नमस्कार! मैं Rxcompute हूँ। कृपया बोलना शुरू करें।' :
        lang === 'mr-IN' ? 'नमस्कार! मी Rxcompute आहे. कृपया बोलायला सुरुवात करा.' :
        'Hello! I am Rxcompute. Please start speaking.';
      setReply(fallbackMsg);
      speak(fallbackMsg, lang);
      welcomeSpokenRef.current = true;
      setTimeout(() => {
        startRecognition(lang);
      }, 2000);
    } finally {
      setIsLoading(false);
    }
  };

  const stopRecognition = () => {
    try { 
      if (recRef.current) {
        recRef.current.stop();
        recRef.current = null;
      }
    } catch (e) {
      console.error('Error stopping recognition:', e);
    }
    setRecognizing(false);
  };

  const startRecognition = async (lang) => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert('Speech Recognition not supported in this browser. Try Chrome on desktop/mobile.');
      return;
    }
    
    stopRecognition();
    
    // Request microphone permission first
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      console.error('Microphone permission denied:', e);
      alert('Please allow microphone access to use voice assistant.');
      return;
    }
    
    const rec = new SR();
    rec.lang = lang;
    rec.continuous = true;
    rec.interimResults = true; // Show interim results for better feedback
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      console.log('Recognition started for language:', lang);
      setRecognizing(true);
      setReply(lang === 'hi-IN' ? 'सुन रहा हूँ...' : lang === 'mr-IN' ? 'ऐकत आहे...' : 'Listening...');
    };
    
    rec.onerror = (e) => {
      console.error('Recognition error:', e.error, e);
      setRecognizing(false);
      
      if (e.error === 'no-speech') {
        // No speech detected, restart listening
        setTimeout(() => {
          if (active && language && !selectingLanguage) {
            startRecognition(language);
          }
        }, 1000);
      } else if (e.error === 'audio-capture') {
        setReply('Microphone not found. Please check your microphone.');
      } else if (e.error === 'not-allowed') {
        setReply('Microphone permission denied. Please allow microphone access.');
      } else {
        // For other errors, try to restart
        setTimeout(() => {
          if (active && language && !selectingLanguage) {
            startRecognition(language);
          }
        }, 2000);
      }
    };
    
    rec.onend = () => {
      console.log('Recognition ended');
      setRecognizing(false);
      // Auto-restart if still active
      if (active && language && !selectingLanguage) {
        setTimeout(() => {
          if (active && language && !selectingLanguage) {
            console.log('Restarting recognition...');
            startRecognition(language);
          }
        }, 500);
      }
    };
    
    rec.onresult = async (e) => {
      console.log('Recognition result received:', e.results.length);
      
      // Process all results
      let finalTranscript = '';
      let interimTranscript = '';
      
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const transcript = e.results[i][0].transcript;
        if (e.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      
      // Show interim results
      if (interimTranscript) {
        setTranscript(interimTranscript);
      }
      
      // Process final results - debounce to prevent glitches
      if (finalTranscript) {
        const text = finalTranscript.trim();
        console.log('Final transcript:', text);
        
        if (text) {
          setTranscript(text);
          // Stop recognition temporarily while processing
          rec.stop();
          
          // Debounce - wait a bit before processing to prevent rapid fire
          await new Promise(resolve => setTimeout(resolve, 300));
          
          await sendToAI(text, lang);
          
          // Restart recognition after processing - with delay to prevent glitches
          setTimeout(() => {
            if (active && language && !selectingLanguage) {
              startRecognition(language);
            }
          }, 1500);
        }
      }
    };

    recRef.current = rec;
    try {
      console.log('Starting recognition with language:', lang);
      rec.start();
    } catch (e) {
      console.error('Error starting recognition:', e);
      setReply('Error starting voice recognition. Please try again.');
    }
  };

  const sendToAI = async (text, lang) => {
    try {
      setIsLoading(true);
      const res = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: lang })
      });
      
      if (!res.ok) {
        throw new Error(`AI error ${res.status}`);
      }
      
      const data = await res.json();
      const responseText = data.reply || '';
      const action = data.action || '';
      
      setReply(responseText);
      
      if (action && action.startsWith('navigate:')) {
        const path = action.replace('navigate:', '');
        speak(responseText, lang);
        setTimeout(() => {
          window.location.href = path;
        }, 1500);
      } else {
        speak(responseText, lang);
      }
    } catch (e) {
      console.error('Error sending to AI:', e);
      const errorMsg = 
        lang === 'hi-IN' ? 'सर्वर से कनेक्ट नहीं हो पाया. कृपया बाद में कोशिश करें.' :
        lang === 'mr-IN' ? 'सर्व्हरशी कनेक्ट होता आले नाही. कृपया नंतर प्रयत्न करा.' :
        'Could not connect to AI server. Please try again later.';
      setReply(errorMsg);
      speak(errorMsg, lang);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = async () => {
    setActive(true);
  };

  const handleClose = () => {
    stopRecognition();
    synthRef.current?.cancel();
    setActive(false);
    // Don't clear language from localStorage - keep it saved
    setTranscript('');
    setReply('');
    setSelectingLanguage(false);
    welcomeSpokenRef.current = false;
    // Don't reset languageSelectionRef - keep it true so it doesn't ask again
  };

  const handleReset = () => {
    // Reset everything including language selection
    localStorage.removeItem('rxcompute_language');
    stopRecognition();
    synthRef.current?.cancel();
    setActive(false);
    setLanguage(null);
    setTranscript('');
    setReply('');
    setSelectingLanguage(false);
    welcomeSpokenRef.current = false;
    languageSelectionRef.current = false;
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!active ? (
        <button 
          onClick={handleStart} 
          className="px-4 py-3 rounded-full bg-emerald-600 text-white shadow-lg hover:bg-emerald-700 flex items-center gap-2 transition-all"
        >
          <Mic className="w-5 h-5" /> Start Rxcompute
        </button>
      ) : selectingLanguage ? (
        <div className="bg-white rounded-xl shadow-2xl p-4 border border-gray-100 w-80">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold text-gray-800">Rxcompute</div>
            <button 
              onClick={handleClose} 
              className="text-sm text-red-500 hover:text-red-600 transition-colors"
            >
              Close
            </button>
          </div>
          <div className="text-sm text-gray-700 mb-2">
            <span className="font-semibold text-emerald-700">Rxcompute:</span> 
            <span className="ml-2">{reply || "Please select your language. Say English, Hindi, or Marathi."}</span>
          </div>
          <div className="min-h-12 text-sm text-gray-700 mb-2 p-2 bg-gray-50 rounded">
            <span className="font-semibold text-gray-600">You:</span> 
            <span className="ml-2">{transcript || 'Listening...'}</span>
          </div>
          {recognizing && (
            <div className="text-xs text-blue-500 mb-2 animate-pulse">
              Listening for your language choice...
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-2xl p-4 border border-gray-100 w-80 max-h-[500px] overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold text-gray-800">Rxcompute</div>
            <button 
              onClick={handleClose} 
              className="text-sm text-red-500 hover:text-red-600 transition-colors"
            >
              Close
            </button>
          </div>
          
          <div className="text-xs text-gray-500 mb-2">
            Language: {language === 'en-IN' ? 'English' : language === 'hi-IN' ? 'हिंदी' : 'मराठी'}
          </div>
          
          {isLoading && (
            <div className="text-xs text-blue-500 mb-2 animate-pulse">
              Processing...
            </div>
          )}
          
          <div className="min-h-12 text-sm text-gray-700 mb-2 p-2 bg-gray-50 rounded">
            <span className="font-semibold text-gray-600">You:</span> 
            <span className="ml-2">{transcript || (recognizing ? 'Listening...' : 'Click Listen to start')}</span>
          </div>
          
          <div className="min-h-12 text-sm text-gray-700 mb-3 p-2 bg-emerald-50 rounded">
            <span className="font-semibold text-emerald-700">Rxcompute:</span> 
            <span className="ml-2">{reply || 'Ready to help...'}</span>
          </div>
          
          {recognizing && (
            <div className="mb-2 flex items-center gap-2 text-xs text-emerald-600">
              <div className="w-2 h-2 bg-emerald-600 rounded-full animate-pulse"></div>
              <span>Listening... Speak now</span>
            </div>
          )}
          
          <div className="flex items-center gap-2">
            {!recognizing ? (
              <button 
                onClick={() => startRecognition(language)} 
                className="flex-1 px-3 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700 flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                disabled={isLoading}
              >
                <Mic className="w-4 h-4"/> {isLoading ? 'Processing...' : 'Listen'}
              </button>
            ) : (
              <button 
                onClick={stopRecognition} 
                className="flex-1 px-3 py-2 rounded bg-red-600 text-white hover:bg-red-700 flex items-center justify-center gap-2 transition-colors"
              >
                <MicOff className="w-4 h-4"/> Stop
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceAgent;
