import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/widgets/shared_widgets.dart';
import '../../../config/routes.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/medicine_model.dart';
import '../bloc/chat_bloc.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _CS();
}

class _CS extends State<ChatScreen> {
  final _tc = TextEditingController();
  final _sc = ScrollController();
  final _picker = ImagePicker();
  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();
  bool _speechReady = false;
  bool _speechInitInProgress = false;
  DateTime? _lastSpeechInitAttempt;
  Set<String> _supportedLocales = <String>{};
  final Set<String> _spokenMessageIds = <String>{};
  bool _spokeVoiceTextHint = false;
  String _pendingTranscript = '';
  String _lastFlushedTranscript = '';
  bool _voiceSessionOpen = false;
  bool _voiceSentForSession = false;

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    _speechReady = await _ensureSpeechReadyFor('hi');
    try {
      await _tts.setLanguage('hi-IN');
      await _tts.setSpeechRate(0.45);
    } catch (_) {}
    if (mounted) setState(() {});
  }

  Future<bool> _ensureSpeechReadyFor(String langCode) async {
    if (_speechReady) return true;
    if (_speechInitInProgress) return false;
    final now = DateTime.now();
    if (_lastSpeechInitAttempt != null && now.difference(_lastSpeechInitAttempt!).inMilliseconds < 1200) {
      return _speechReady;
    }
    _lastSpeechInitAttempt = now;
    _speechInitInProgress = true;
    try {
      final mic = await Permission.microphone.request();
      if (!mic.isGranted) {
        _speechReady = false;
        return false;
      }
      _speechReady = await _speech.initialize(
        onStatus: (status) {
          if ((status == 'done' || status == 'notListening') && mounted) {
            final bloc = context.read<ChatBloc>();
            if (bloc.state.isRecording) {
              bloc.add(ToggleRecordingEvent());
            }
            _flushPendingTranscript();
          }
        },
        onError: (_) {},
      );
      if (_speechReady) {
        try {
          final locales = await _speech.locales();
          _supportedLocales = locales.map((e) => e.localeId).toSet();
        } catch (_) {}
      }
      return _speechReady;
    } catch (_) {
      _speechReady = false;
      return false;
    } finally {
      _speechInitInProgress = false;
    }
  }

  String _localeFor(String langCode) {
    final c = (langCode).toLowerCase();
    if (c == 'hi') return 'hi_IN';
    if (c == 'mr') return 'mr_IN';
    return 'en_IN';
  }

  String _bestLocaleFor(String langCode) {
    final preferred = _localeFor(langCode);
    if (_supportedLocales.isEmpty || _supportedLocales.contains(preferred)) {
      return preferred;
    }
    if (_supportedLocales.contains('en_IN')) return 'en_IN';
    if (_supportedLocales.contains('en_US')) return 'en_US';
    return _supportedLocales.first;
  }

  @override
  void dispose() {
    _speech.stop();
    _tts.stop();
    _tc.dispose();
    _sc.dispose();
    super.dispose();
  }

  void _send() {
    final t = _tc.text.trim();
    if (t.isEmpty) return;
    context.read<ChatBloc>().add(SendMessageEvent(t));
    _tc.clear();
    _scrollEnd();
  }

  Future<void> _pickAndUploadPrescription() async {
    final xfile = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (xfile == null) return;
    if (!mounted) return;
    context.read<ChatBloc>().add(UploadPrescriptionEvent(xfile.path));
  }

  Future<void> _toggleVoice(ChatState state) async {
    final ready = await _ensureSpeechReadyFor(state.languageCode);
    if (!ready) {
      await _speakText('Voice recognition is not available right now.');
      return;
    }
    if (state.isRecording) {
      await _speech.stop();
      _voiceSessionOpen = false;
      if (mounted) context.read<ChatBloc>().add(ToggleRecordingEvent());
      return;
    }

    // Ensure bot TTS doesn't occupy the audio session while user starts speaking.
    try {
      await _tts.stop();
    } catch (_) {}
    context.read<ChatBloc>().add(ToggleRecordingEvent());
    _pendingTranscript = '';
    _voiceSessionOpen = true;
    _voiceSentForSession = false;
    try {
      await _speech.cancel();
    } catch (_) {}
    await _speech.listen(
      onResult: (result) {
        _pendingTranscript = result.recognizedWords;
        setState(() {
          _tc.text = result.recognizedWords;
          _tc.selection = TextSelection.fromPosition(TextPosition(offset: _tc.text.length));
        });
        final spoken = result.recognizedWords.trim();
        if (result.finalResult && spoken.isNotEmpty && !_voiceSentForSession) {
          _voiceSentForSession = true;
          _lastFlushedTranscript = spoken.toLowerCase();
          _send();
        }
      },
      listenMode: stt.ListenMode.dictation,
      localeId: _bestLocaleFor(state.languageCode),
      listenFor: const Duration(seconds: 20),
      pauseFor: const Duration(seconds: 4),
      partialResults: true,
    );
  }

  void _flushPendingTranscript() {
    if (!_voiceSessionOpen) return;
    _voiceSessionOpen = false;
    if (_voiceSentForSession) return;
    final text = _pendingTranscript.trim();
    if (text.isEmpty) return;
    final norm = text.toLowerCase();
    if (norm == _lastFlushedTranscript) return;
    _lastFlushedTranscript = norm;
    setState(() {
      _tc.text = text;
      _tc.selection = TextSelection.fromPosition(TextPosition(offset: _tc.text.length));
    });
    if (text.length >= 2) {
      _voiceSentForSession = true;
      _send();
    }
  }

  void _scrollEnd() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_sc.hasClients) _sc.animateTo(_sc.position.maxScrollExtent + 100, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
      });

  Future<void> _speakText(String text) async {
    if (text.trim().isEmpty) return;
    final speakable = _normalizeSpeechText(text);
    try {
      await _tts.speak(speakable);
    } catch (_) {}
  }

  String _normalizeSpeechText(String input) {
    var out = input;
    out = out.replaceAll('€', ' rupees ');
    out = out.replaceAll(RegExp(r'\beur\b', caseSensitive: false), 'rupees');
    out = out.replaceAll(RegExp(r'\beuro(s)?\b', caseSensitive: false), 'rupees');
    out = out.replaceAll(RegExp(r'\s+'), ' ').trim();
    return out;
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return BlocConsumer<ChatBloc, ChatState>(
      listener: (context, state) async {
        _scrollEnd();
        if (state.isRecording) return;
        if (!_spokeVoiceTextHint && state.messages.isNotEmpty) {
          _spokeVoiceTextHint = true;
          await _speakText('You can talk with voice or text in chat. Tap the mic to speak.');
        }
        if (state.messages.isEmpty) return;
        final last = state.messages.last;
        if (last.isUser) return;
        if (_spokenMessageIds.contains(last.id)) return;
        _spokenMessageIds.add(last.id);
        await _speakText(last.text);
      },
      builder: (context, state) {
        return Scaffold(
          backgroundColor: r.bg,
          body: SafeArea(
            child: Column(children: [
              Container(
                padding: const EdgeInsets.fromLTRB(20, 10, 20, 12),
                decoration: BoxDecoration(color: r.bg, border: Border(bottom: BorderSide(color: r.border, width: 0.5))),
                child: Row(children: [
                  const RxLogo(size: 18),
                  const SizedBox(width: 10),
                  Container(width: 6, height: 6, decoration: const BoxDecoration(color: C.ok, shape: BoxShape.circle)),
                  const SizedBox(width: 5),
                  Text('ONLINE', style: GoogleFonts.outfit(color: C.ok, fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                  const Spacer(),
                  Icon(Icons.more_horiz_rounded, color: r.text3, size: 20),
                ]),
              ),
              Expanded(
                child: ListView.builder(
                  controller: _sc,
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  itemCount: state.messages.length + (state.isTyping ? 1 : 0),
                  itemBuilder: (_, i) => i == state.messages.length && state.isTyping ? _typB(r) : _build(state.messages[i], r),
                ),
              ),
              if (state.awaitingLanguage)
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
                  child: Row(
                    children: [
                      Expanded(child: _langBtn('Hindi', () => context.read<ChatBloc>().add(SendMessageEvent('Hindi')), r)),
                      const SizedBox(width: 8),
                      Expanded(child: _langBtn('English', () => context.read<ChatBloc>().add(SendMessageEvent('English')), r)),
                    ],
                  ),
                ),
              Container(
                padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                decoration: BoxDecoration(color: r.card, border: Border(top: BorderSide(color: r.border, width: 0.5))),
                child: SafeArea(
                  top: false,
                  child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                    GestureDetector(
                      onTap: () => _toggleVoice(state),
                      child: Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(color: state.isRecording ? C.rx : r.surface, borderRadius: BorderRadius.circular(12)),
                        child: Icon(state.isRecording ? Icons.stop_rounded : Icons.mic_rounded, color: state.isRecording ? Colors.white : r.text1, size: 18),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Container(
                        constraints: const BoxConstraints(maxHeight: 120),
                        decoration: BoxDecoration(color: r.surface, borderRadius: BorderRadius.circular(20)),
                        child: TextField(
                          controller: _tc,
                          maxLines: 4,
                          minLines: 1,
                          textInputAction: TextInputAction.send,
                          onSubmitted: (_) => _send(),
                          onChanged: (_) => setState(() {}),
                          style: GoogleFonts.outfit(color: r.text1, fontSize: 14),
                          decoration: InputDecoration(
                            hintText: state.awaitingLanguage ? 'Select language first...' : 'Type or speak your message...',
                            hintStyle: TextStyle(color: r.text3),
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                            filled: false,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    GestureDetector(
                      onTap: _tc.text.trim().isNotEmpty ? _send : null,
                      child: Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(color: _tc.text.trim().isNotEmpty ? C.rx : r.surface, borderRadius: BorderRadius.circular(12)),
                        child: Icon(Icons.arrow_upward_rounded, color: _tc.text.trim().isNotEmpty ? Colors.white : r.text3, size: 18),
                      ),
                    ),
                  ]),
                ),
              ),
            ]),
          ),
        );
      },
    );
  }

  Widget _av() => Container(
        width: 26,
        height: 26,
        margin: const EdgeInsets.only(top: 2),
        decoration: BoxDecoration(color: C.compute.withOpacity(context.rx.dark ? 0.12 : 0.06), borderRadius: BorderRadius.circular(8)),
        child: Center(child: Text('Rx', style: GoogleFonts.dmSerifDisplay(color: C.compute, fontSize: 11))),
      );

  Widget _build(ChatMessage m, Rx r) {
    if (m.isUser) return _uB(m, r);
    switch (m.type) {
      case ChatMessageType.meds:
        return _medR(m, r);
      case ChatMessageType.options:
        return _optR(m, r);
      case ChatMessageType.safety:
        return _safR(m, r);
      case ChatMessageType.confirmed:
        return _ordR(m, r);
      default:
        return _aiB(m, r);
    }
  }

  Widget _uB(ChatMessage m, Rx r) => Padding(
        padding: const EdgeInsets.only(bottom: 18, left: 56),
        child: Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(color: C.rx, borderRadius: BorderRadius.only(topLeft: Radius.circular(16), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(4))),
            child: Text(m.text, style: GoogleFonts.outfit(color: Colors.white, fontSize: 14, height: 1.5)),
          ),
          const SizedBox(height: 4),
          Text(_ft(m.timestamp), style: TextStyle(color: r.text3, fontSize: 9)),
        ]),
      );

  Widget _aiB(ChatMessage m, Rx r) => Padding(
        padding: const EdgeInsets.only(bottom: 18, right: 44),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _av(),
          const SizedBox(width: 10),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: r.card,
                  borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
                  border: Border.all(color: r.border.withOpacity(0.4)),
                ),
                child: Text(m.text, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, height: 1.5)),
              ),
              const SizedBox(height: 4),
              Text(_ft(m.timestamp), style: TextStyle(color: r.text3, fontSize: 9)),
            ]),
          ),
        ]),
      );

  Widget _typB(Rx r) => Padding(
        padding: const EdgeInsets.only(bottom: 18, right: 44),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _av(),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              color: r.card,
              borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
            ),
            child: const TypingDots(),
          ),
        ]),
      );

  Widget _medR(ChatMessage m, Rx r) => Padding(
        padding: const EdgeInsets.only(bottom: 18, right: 20),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _av(),
          const SizedBox(width: 10),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: r.card,
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
                border: Border.all(color: r.border.withOpacity(0.4)),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(m.text, style: GoogleFonts.outfit(color: r.text2, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
                const SizedBox(height: 14),
                ...m.medicines!.map(
                  (med) => _MC(
                    med: med,
                    onQuantityChanged: (q) {
                      setState(() {});
                      context.read<ChatBloc>().add(UpdateDraftStripsEvent(q));
                    },
                  ),
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: r.okBg, borderRadius: BorderRadius.circular(8)),
                  child: Row(children: [
                    Icon(Icons.check_circle_rounded, color: C.ok, size: 16),
                    const SizedBox(width: 8),
                    Text('ALL SAFETY CHECKS PASSED', style: GoogleFonts.outfit(color: C.ok, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.8)),
                  ]),
                ),
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: r.surface, borderRadius: BorderRadius.circular(10)),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('ORDER SUMMARY', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                    const SizedBox(height: 10),
                    ...m.medicines!.map((med) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                            Expanded(child: Text('${med.name} × ${med.quantity}', style: TextStyle(color: r.text2, fontSize: 13), overflow: TextOverflow.ellipsis)),
                            Text('₹${(med.price * med.quantity).toStringAsFixed(2)}', style: TextStyle(color: r.text2, fontSize: 13)),
                          ]),
                        )),
                    Container(height: 1, color: r.border, margin: const EdgeInsets.symmetric(vertical: 8)),
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      Text('Total', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 20)),
                      Text('₹${m.medicines!.fold<double>(0, (s, med) => s + med.price * med.quantity).toStringAsFixed(2)}', style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 20)),
                    ]),
                  ]),
                ),
                const SizedBox(height: 14),
                RxBtn(label: 'Continue in Chat', onPressed: () => context.read<ChatBloc>().add(SendMessageEvent('yes'))),
                const SizedBox(height: 6),
                Center(child: TextButton(onPressed: () {}, child: Text('CANCEL', style: GoogleFonts.outfit(color: r.text3, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 1)))),
              ]),
            ),
          ),
        ]),
      );

  Widget _optR(ChatMessage m, Rx r) => Padding(
        padding: const EdgeInsets.only(bottom: 18, right: 20),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _av(),
          const SizedBox(width: 10),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: r.card,
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
                border: Border.all(color: r.border.withOpacity(0.4)),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(m.text, style: GoogleFonts.outfit(color: r.text2, fontSize: 13, fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                ...m.medicines!.asMap().entries.map((entry) {
                  final idx = entry.key;
                  final med = entry.value;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: r.surface, borderRadius: BorderRadius.circular(10)),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('${idx + 1}. ${med.name}', style: GoogleFonts.outfit(color: r.text1, fontSize: 13, fontWeight: FontWeight.w600)),
                              const SizedBox(height: 4),
                              Text('PZN: ${med.pzn} · ${med.formattedPrice}', style: GoogleFonts.outfit(color: r.text3, fontSize: 11)),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        SizedBox(
                          width: 88,
                          child: RxBtn(
                            label: 'Select',
                            onPressed: () => context.read<ChatBloc>().add(SelectMedicineEvent(med)),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
                Text(
                  'Type option number (1, 2, 3...) ya Select button dabao.',
                  style: GoogleFonts.outfit(color: r.text3, fontSize: 11),
                ),
              ]),
            ),
          ),
        ]),
      );

  Widget _safR(ChatMessage m, Rx r) => Padding(
        padding: const EdgeInsets.only(bottom: 18, right: 20),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _av(),
          const SizedBox(width: 10),
          Expanded(
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: r.card,
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
                border: Border.all(color: r.border.withOpacity(0.4)),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(m.text, style: GoogleFonts.outfit(color: r.text2, fontSize: 12, fontWeight: FontWeight.w600)),
                const SizedBox(height: 14),
                if (m.medicines != null) ...m.medicines!.map((med) => _MC(med: med)),
                ...(m.warnings ?? const <SafetyWarning>[]).map((w) => Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: r.errBg, borderRadius: BorderRadius.circular(10), border: const Border(left: BorderSide(color: C.err, width: 3))),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Row(children: [
                          const Icon(Icons.shield_rounded, color: C.err, size: 15),
                          const SizedBox(width: 8),
                          Text('PRESCRIPTION REQUIRED', style: GoogleFonts.outfit(color: C.err, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.8)),
                        ]),
                        const SizedBox(height: 8),
                        Text(w.message, style: GoogleFonts.outfit(color: r.text1, fontSize: 13, height: 1.5)),
                        const SizedBox(height: 12),
                        RxBtn(label: 'Upload Prescription', icon: Icons.upload_rounded, color: C.err, onPressed: _pickAndUploadPrescription),
                      ]),
                    )),
                if ((m.warnings ?? const <SafetyWarning>[]).isEmpty)
                  Text(
                    'No warning details available. Please re-run the safety check.',
                    style: GoogleFonts.outfit(color: r.text3, fontSize: 12),
                  ),
              ]),
            ),
          ),
        ]),
      );

  Widget _ordR(ChatMessage m, Rx r) {
    final o = m.order;
    if (o == null) return _aiB(m, r);
    return Padding(
      padding: const EdgeInsets.only(bottom: 18, right: 20),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _av(),
        const SizedBox(width: 10),
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: r.card,
              borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(16), bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16)),
              border: const Border(left: BorderSide(color: C.ok, width: 3)),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: r.okBg, borderRadius: BorderRadius.circular(10)),
                child: Row(children: [
                  const Icon(Icons.check_circle_rounded, color: C.ok, size: 20),
                  const SizedBox(width: 10),
                  Text('Order Placed', style: GoogleFonts.dmSerifDisplay(color: C.ok, fontSize: 18)),
                ]),
              ),
              const SizedBox(height: 14),
              Row(children: [
                Text('ORDER ID  ', style: GoogleFonts.outfit(color: r.text3, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 1)),
                Mono(o.orderUid, size: 12, color: r.text1),
              ]),
              const SizedBox(height: 6),
              Text(o.formattedTotal, style: GoogleFonts.dmSerifDisplay(color: r.text1, fontSize: 22)),
              const SizedBox(height: 14),
              RxBtn(label: 'Track Order', icon: Icons.local_shipping_rounded, color: C.compute, onPressed: () => Navigator.pushNamed(context, AppRoutes.orderTracking)),
            ]),
          ),
        ),
      ]),
    );
  }

  String _ft(DateTime d) => '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

  Widget _langBtn(String label, VoidCallback onTap, Rx r) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: r.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: r.border),
        ),
        child: Center(
          child: Text(label, style: GoogleFonts.outfit(color: r.text1, fontWeight: FontWeight.w600)),
        ),
      ),
    );
  }
}

class _MC extends StatefulWidget {
  final MedicineModel med;
  final ValueChanged<int>? onQuantityChanged;
  const _MC({required this.med, this.onQuantityChanged});
  @override
  State<_MC> createState() => _MCS();
}

class _MCS extends State<_MC> {
  late int _q;
  @override
  void initState() {
    super.initState();
    _q = widget.med.quantity;
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    final m = widget.med;
    final sc = m.stock == 0 ? C.err : m.stock < 10 ? C.warn : C.ok;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: r.surface, borderRadius: BorderRadius.circular(10)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if ((m.imageUrl ?? '').isNotEmpty) ...[
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.network(
              m.imageUrl!,
              height: 120,
              width: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const SizedBox.shrink(),
            ),
          ),
          const SizedBox(height: 10),
        ],
        Text(m.name, style: GoogleFonts.outfit(color: r.text1, fontSize: 14, fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        Text('PZN: ${m.pzn}  ·  ${m.formattedPrice}  ·  ${m.package ?? ''}', style: GoogleFonts.outfit(color: r.text3, fontSize: 11)),
        const SizedBox(height: 8),
        Row(children: [
          Container(width: 6, height: 6, decoration: BoxDecoration(color: sc, shape: BoxShape.circle)),
          const SizedBox(width: 6),
          Text(m.stock == 0 ? 'OUT OF STOCK' : m.stock < 10 ? 'LOW (${m.stock})' : 'IN STOCK (${m.stock})',
              style: GoogleFonts.outfit(color: sc, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.8)),
          if (m.rxRequired) ...[const Spacer(), RxBadge(text: 'Rx', color: C.err, icon: Icons.shield_rounded)],
        ]),
        const SizedBox(height: 10),
        Row(mainAxisAlignment: MainAxisAlignment.end, children: [
          _qb(Icons.remove, () {
            if (_q > 1) {
              setState(() => _q--);
              widget.med.quantity = _q;
              widget.onQuantityChanged?.call(_q);
            }
          }),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 14), child: Text('$_q', style: GoogleFonts.outfit(color: r.text1, fontSize: 15, fontWeight: FontWeight.w600))),
          _qb(Icons.add, () {
            setState(() => _q++);
            widget.med.quantity = _q;
            widget.onQuantityChanged?.call(_q);
          }),
        ]),
      ]),
    );
  }

  Widget _qb(IconData ic, VoidCallback fn) {
    final r = context.rx;
    return GestureDetector(
      onTap: fn,
      child: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(color: r.card, borderRadius: BorderRadius.circular(8), border: Border.all(color: r.border)),
        child: Icon(ic, size: 14, color: r.text1),
      ),
    );
  }
}
