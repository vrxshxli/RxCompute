import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/rx_theme_ext.dart';
import '../../../core/services/local_notification_service.dart';
import '../../../data/providers/api_provider.dart';
import '../../../data/models/notification_model.dart';
import '../../../data/repositories/medicine_repository.dart';
import '../../../data/repositories/notification_repository.dart';
import '../../../data/repositories/order_repository.dart';
import '../../../data/repositories/user_repository.dart';
import '../../../data/repositories/prediction_repository.dart';
import '../bloc/home_bloc.dart';
import 'home_tab.dart';
import '../../chat/screens/chat_screen.dart';
import '../../medicine/screens/medicine_brain_screen.dart';
import '../../profile/screens/profile_screen.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});
  @override
  State<MainShell> createState() => _MS();
}

class _MS extends State<MainShell> with WidgetsBindingObserver {
  int _i = 0;
  final _screens = const [HomeTab(), ChatScreen(), MedicineBrainScreen(), ProfileScreen()];
  final UserRepository _userRepository = UserRepository();
  StreamSubscription<String>? _tokenSub;
  StreamSubscription<RemoteMessage>? _onMessageSub;
  StreamSubscription<RemoteMessage>? _onMessageOpenSub;
  final AudioPlayer _audioPlayer = AudioPlayer();
  final FlutterTts _tts = FlutterTts();
  final stt.SpeechToText _speech = stt.SpeechToText();
  final MedicineRepository _medicineRepository = MedicineRepository();
  final NotificationRepository _notificationRepository = NotificationRepository();
  final OrderRepository _orderRepository = OrderRepository();
  final PredictionRepository _predictionRepository = PredictionRepository();
  final ApiProvider _apiProvider = ApiProvider();
  bool _speechReady = false;
  bool _isListening = false;
  String _speechLocale = 'en_IN';
  String _voiceLanguage = 'en-IN';
  String _lastHeard = '';
  Timer? _notifPoller;
  int _lastSeenNotifId = 0;
  bool _didInitialNotificationSpeak = false;
  final Set<int> _spokenNotifIds = <int>{};
  final Map<String, DateTime> _speakDedupe = <String, DateTime>{};
  bool _refillPromptInProgress = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initPushToken();
    _initVoiceAssistant();
    _startNotificationVoiceFeed();
  }

  Future<void> _initPushToken() async {
    try {
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(alert: true, badge: true, sound: true);
      debugPrint('🔔 Notification permission: ${settings.authorizationStatus}');
      final token = await messaging.getToken();
      if (token != null && token.isNotEmpty) {
        debugPrint('🔑 FCM token acquired');
        await _userRepository.updateProfile(pushToken: token);
      } else {
        debugPrint('⚠️ FCM token missing');
      }
      _tokenSub = FirebaseMessaging.instance.onTokenRefresh.listen((newToken) async {
        if (newToken.isNotEmpty) {
          debugPrint('🔄 FCM token refreshed');
          await _userRepository.updateProfile(pushToken: newToken);
        }
      });
      _onMessageSub = FirebaseMessaging.onMessage.listen((message) {
        if (!mounted) return;
        final title = message.notification?.title ?? 'RxCompute';
        final body = message.notification?.body ?? 'New update available';
        final lowered = '$title $body'.toLowerCase();
        final isSafety = lowered.contains('safety');
        final isRefill = lowered.contains('refill');
        final isOrder = lowered.contains('order');
        LocalNotificationService.show(title: title, body: body, id: DateTime.now().millisecondsSinceEpoch.remainder(1000000));
        _announceMessage(title: title, body: body, isSafety: isSafety, isRefill: isRefill, isOrder: isOrder);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$title: $body')),
        );
        context.read<HomeBloc>().add(LoadHomeDataEvent());
      });
      _onMessageOpenSub = FirebaseMessaging.onMessageOpenedApp.listen((_) {
        if (!mounted) return;
        setState(() => _i = 0);
        _pollAndSpeakNotifications(forceSpeakRefillOnOpen: true);
        context.read<HomeBloc>().add(LoadHomeDataEvent());
        _maybePromptRefillConfirmation(trigger: 'notification_tap');
      });
    } catch (e) {
      debugPrint('⚠️ Push init failed: $e');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _pollAndSpeakNotifications(forceSpeakRefillOnOpen: true);
      _maybePromptRefillConfirmation(trigger: 'app_resume');
    }
  }

  Future<void> _startNotificationVoiceFeed() async {
    await _pollAndSpeakNotifications(forceSpeakRefillOnOpen: true);
    await _maybePromptRefillConfirmation(trigger: 'app_open');
    _notifPoller?.cancel();
    _notifPoller = Timer.periodic(const Duration(seconds: 12), (_) {
      _pollAndSpeakNotifications();
    });
  }

  Future<void> _maybePromptRefillConfirmation({required String trigger}) async {
    if (!mounted || _refillPromptInProgress) return;
    _refillPromptInProgress = true;
    try {
      final profile = await _userRepository.getProfile();
      final userId = profile.id;
      final data = await _predictionRepository.getRefillCandidates();
      final rows = (data['candidates'] is List) ? (data['candidates'] as List) : const [];
      if (rows.isEmpty) return;

      Map<String, dynamic>? chosen;
      for (final r in rows) {
        if (r is! Map) continue;
        final m = Map<String, dynamic>.from(r);
        final risk = (m['risk_level'] ?? '').toString().toLowerCase();
        if (risk == 'overdue' || risk == 'high') {
          chosen = m;
          break;
        }
      }
      final firstRow = rows.first;
      if (chosen == null && firstRow is Map) {
        chosen = Map<String, dynamic>.from(firstRow);
      }
      if (chosen == null) return;

      final medicineId = chosen['medicine_id'];
      final medicationId = chosen['medication_id'];
      final medicineName = (chosen['medicine_name'] ?? 'Medicine').toString();
      final dayKey = DateTime.now().toIso8601String().substring(0, 10);
      final promptKey = 'refill_prompt_seen_${userId}_${medicineId ?? medicationId ?? medicineName}_$dayKey';
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getBool(promptKey) == true) return;
      await prefs.setBool(promptKey, true);

      final qtyCtrl = TextEditingController(text: '1');
      bool takeRefill = true;
      bool confirmed = false;
      if (!mounted) return;
      final accepted = await showDialog<bool>(
            context: context,
            barrierDismissible: false,
            builder: (ctx) => StatefulBuilder(
              builder: (ctx, setD) => AlertDialog(
                title: const Text('Refill Confirmation'),
                content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('$medicineName is due for refill.'),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Checkbox(value: takeRefill, onChanged: (v) => setD(() => takeRefill = v == true)),
                        const Expanded(child: Text('Take this refill now')),
                      ],
                    ),
                    TextField(
                      controller: qtyCtrl,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Strips/units'),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Checkbox(value: confirmed, onChanged: (v) => setD(() => confirmed = v == true)),
                        const Expanded(child: Text('I confirm this refill request')),
                      ],
                    ),
                  ],
                ),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Not now')),
                  ElevatedButton(
                    onPressed: (!takeRefill || !confirmed) ? null : () => Navigator.pop(ctx, true),
                    child: const Text('Confirm'),
                  ),
                ],
              ),
            ),
          ) ??
          false;
      if (!accepted || !mounted) return;
      final qty = int.tryParse(qtyCtrl.text.trim()) ?? 1;
      final res = await _predictionRepository.confirmRefill(
        medicationId: medicationId is int ? medicationId : null,
        medicineId: medicineId is int ? medicineId : null,
        medicineName: medicineName,
        quantityUnits: qty < 1 ? 1 : qty,
        confirmationSource: 'popup_$trigger',
      );
      final uid = (res['order_uid'] ?? '').toString();
      await _speak(uid.isNotEmpty ? 'Refill order $uid created successfully.' : 'Refill order created successfully.');
      if (!mounted) return;
      context.read<HomeBloc>().add(LoadHomeDataEvent());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Refill confirm failed: $e')),
        );
      }
    } finally {
      _refillPromptInProgress = false;
    }
  }

  Future<void> _pollAndSpeakNotifications({bool forceSpeakRefillOnOpen = false}) async {
    try {
      final list = await _notificationRepository.getNotifications();
      if (list.isEmpty) return;
      if (mounted) {
        context.read<HomeBloc>().add(LoadHomeDataEvent());
      }
      final sorted = [...list]..sort((a, b) => b.id.compareTo(a.id));
      final maxId = sorted.first.id;

      if (!_didInitialNotificationSpeak || forceSpeakRefillOnOpen) {
        _didInitialNotificationSpeak = true;
        final latestRefill = sorted.cast<NotificationModel?>().firstWhere(
              (n) => n?.type == NotificationType.refill,
              orElse: () => null,
            );
        final latestOrder = sorted.cast<NotificationModel?>().firstWhere(
              (n) => n?.type == NotificationType.order,
              orElse: () => null,
            );
        if (latestRefill != null) {
          _announceFromModel(latestRefill, highPriority: true);
        }
        if (latestOrder != null && latestOrder.id > _lastSeenNotifId) {
          _announceFromModel(latestOrder);
        }
        _lastSeenNotifId = max(_lastSeenNotifId, maxId);
        return;
      }

      final fresh = sorted.where((n) => n.id > _lastSeenNotifId).toList().reversed.toList();
      for (final n in fresh.take(4)) {
        _announceFromModel(n);
      }
      _lastSeenNotifId = max(_lastSeenNotifId, maxId);
    } catch (_) {}
  }

  void _announceFromModel(NotificationModel n, {bool highPriority = false}) {
    if (_spokenNotifIds.contains(n.id)) return;
    _spokenNotifIds.add(n.id);
    final isSafety = n.type == NotificationType.safety;
    final isRefill = n.type == NotificationType.refill;
    final isOrder = n.type == NotificationType.order;
    _announceMessage(
      title: n.title,
      body: n.body,
      isSafety: isSafety,
      isRefill: isRefill,
      isOrder: isOrder,
      highPriority: highPriority,
    );
  }

  void _announceMessage({
    required String title,
    required String body,
    bool isSafety = false,
    bool isRefill = false,
    bool isOrder = false,
    bool highPriority = false,
  }) {
    final isScheduler = ('$title $body').toLowerCase().contains('scheduler');
    final key = '${title.trim()}|${body.trim()}'.toLowerCase();
    final now = DateTime.now();
    final last = _speakDedupe[key];
    if (last != null && now.difference(last).inSeconds < 45) {
      return;
    }
    _speakDedupe[key] = now;

    _audioPlayer.play(AssetSource('sounds/rx_tune.wav'));
    if (isSafety || highPriority) {
      Future.delayed(const Duration(milliseconds: 900), () {
        _audioPlayer.play(AssetSource('sounds/rx_tune.wav'));
      });
    }
    if (isSafety && isScheduler) {
      _speak('Scheduler agent alert. $title. $body');
      return;
    }
    if (isSafety) {
      _speak('Safety alert. $title. $body');
      return;
    }
    if (isRefill) {
      _speak('Refill reminder. $title. $body');
      return;
    }
    if (isOrder) {
      _announceOrderUpdate(title, body);
      return;
    }
    _speak('$title. $body');
  }

  Future<void> _announceOrderUpdate(String title, String body) async {
    String medsPart = '';
    try {
      final orders = await _orderRepository.getOrders();
      final uid = _extractOrderUid('$title $body');
      dynamic target;
      if (uid == null) {
        target = orders.isNotEmpty ? orders.first : null;
      } else {
        for (final o in orders) {
          if (o.orderUid.toUpperCase() == uid.toUpperCase()) {
            target = o;
            break;
          }
        }
      }
      if (target != null && target.items.isNotEmpty) {
        final names = target.items.map((e) => e.name).where((e) => e.trim().isNotEmpty).toList();
        if (names.isNotEmpty) {
          medsPart = names.take(2).join(', ');
        }
      }
    } catch (_) {}
    final cleanedBody = body
        .replaceAll(RegExp(r'ORD-\d{8}-[A-Z0-9]+', caseSensitive: false), 'your order')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
    if (medsPart.isNotEmpty) {
      await _speak('Order update for medicines $medsPart. $cleanedBody');
      return;
    }
    await _speak('Order update. $cleanedBody');
  }

  String? _extractOrderUid(String text) {
    final m = RegExp(r'ORD-\d{8}-[A-Z0-9]+', caseSensitive: false).firstMatch(text);
    return m?.group(0);
  }

  Future<void> _initVoiceAssistant() async {
    try {
      _speechReady = await _speech.initialize();
      await _tts.setLanguage(_voiceLanguage);
      await _tts.setSpeechRate(0.45);
    } catch (_) {
      _speechReady = false;
    }
  }

  Future<void> _speak(String text) async {
    if (text.trim().isEmpty) return;
    try {
      await _tts.setLanguage(_voiceLanguage);
      await _tts.speak(text);
    } catch (_) {}
  }

  void _setVoiceLanguage(String code) {
    setState(() {
      _voiceLanguage = code;
      _speechLocale = code == 'hi-IN' ? 'hi_IN' : 'en_IN';
    });
    _speak(code == 'hi-IN' ? 'भाषा हिंदी पर सेट हो गई है।' : 'Language set to English.');
  }

  Future<void> _handleVoiceCommand(String raw) async {
    final txt = raw.toLowerCase().trim();
    if (txt.isEmpty) return;
    setState(() => _lastHeard = raw);

    bool says(List<String> keys) => keys.any((k) => txt.contains(k));

    if (says(['help', 'madad', 'सहायता'])) {
      await _speak(_voiceLanguage == 'hi-IN'
          ? 'आप बोल सकते हैं: ओपन होम, ओपन चैट, ओपन मेड्स, ओपन प्रोफाइल, सेफ्टी चेक फॉर पैरासिटामोल क्वांटिटी 2, रीफिल कन्फर्म ओमेगा 3 क्वांटिटी 2, या रीड लेटेस्ट सेफ्टी अलर्ट।'
          : 'You can say: open home, open chat, open meds, open profile, check safety for paracetamol quantity 2, confirm refill omega 3 quantity 2, or read latest safety alert.');
      return;
    }

    if (says(['open home', 'go to home', 'home kholo', 'होम'])) {
      setState(() => _i = 0);
      await _speak(_voiceLanguage == 'hi-IN' ? 'होम खोल दिया।' : 'Opening home.');
      return;
    }
    if (says(['open chat', 'go to chat', 'chat kholo', 'चैट'])) {
      setState(() => _i = 1);
      await _speak(_voiceLanguage == 'hi-IN' ? 'चैट खोल दिया।' : 'Opening chat.');
      return;
    }
    if (says(['open meds', 'open medicine', 'go to meds', 'meds kholo', 'मेडिसिन'])) {
      setState(() => _i = 2);
      await _speak(_voiceLanguage == 'hi-IN' ? 'मेडिसिन सेक्शन खोल दिया।' : 'Opening medicines.');
      return;
    }
    if (says(['open profile', 'go to profile', 'profile kholo', 'प्रोफाइल'])) {
      setState(() => _i = 3);
      await _speak(_voiceLanguage == 'hi-IN' ? 'प्रोफाइल खोल दिया।' : 'Opening profile.');
      return;
    }

    if (says(['read latest safety alert', 'latest safety', 'सेफ्टी अलर्ट'])) {
      try {
        final notifs = await _notificationRepository.getNotifications();
        final safety = notifs.firstWhere(
          (n) => n.type.name.toLowerCase() == 'safety',
          orElse: () => throw Exception(),
        );
        await _speak('${safety.title}. ${safety.body}');
      } catch (_) {
        await _speak(_voiceLanguage == 'hi-IN' ? 'कोई सेफ्टी अलर्ट नहीं मिला।' : 'No safety alert found.');
      }
      return;
    }

    if (says(['check safety for', 'safety check', 'सेफ्टी चेक'])) {
      final qtyMatch = RegExp(r'(quantity|qty)\s+(\d+)').firstMatch(txt);
      final qty = qtyMatch != null ? int.tryParse(qtyMatch.group(2) ?? '1') ?? 1 : 1;
      String medQuery = txt
          .replaceAll(RegExp(r'check safety for|safety check|quantity\s+\d+|qty\s+\d+'), '')
          .replaceAll(RegExp(r'सेफ्टी चेक|के लिए|का|की|करो|करिए'), '')
          .trim();
      if (medQuery.isEmpty) {
        await _speak(_voiceLanguage == 'hi-IN' ? 'कृपया मेडिसिन का नाम बोलें।' : 'Please tell the medicine name.');
        return;
      }
      try {
        final meds = await _medicineRepository.getMedicines(search: medQuery);
        if (meds.isEmpty) {
          await _speak(_voiceLanguage == 'hi-IN' ? '$medQuery नहीं मिला।' : '$medQuery not found.');
          return;
        }
        final med = meds.first;
        final res = await _apiProvider.dio.post(
          '/safety/check-single/${med.id}',
          queryParameters: {'quantity': qty},
        );
        final data = res.data as Map<String, dynamic>;
        final summary = (data['safety_summary'] ?? '').toString();
        final blocked = data['blocked'] == true;
        if (blocked) {
          _audioPlayer.play(AssetSource('sounds/rx_tune.wav'));
          Future.delayed(const Duration(milliseconds: 900), () {
            _audioPlayer.play(AssetSource('sounds/rx_tune.wav'));
          });
        }
        await _speak(summary.isNotEmpty ? summary : (_voiceLanguage == 'hi-IN' ? 'सेफ्टी चेक पूरा हुआ।' : 'Safety check completed.'));
      } catch (_) {
        await _speak(_voiceLanguage == 'hi-IN' ? 'सेफ्टी चेक में समस्या आई।' : 'Safety check failed.');
      }
      return;
    }

    if (says(['confirm refill', 'refill confirm', 'reorder refill', 'रीफिल कन्फर्म'])) {
      final qtyMatch = RegExp(r'(quantity|qty)\s+(\d+)').firstMatch(txt);
      final qty = qtyMatch != null ? int.tryParse(qtyMatch.group(2) ?? '1') ?? 1 : 1;
      String medQuery = txt
          .replaceAll(RegExp(r'confirm refill|refill confirm|reorder refill|quantity\s+\d+|qty\s+\d+'), ' ')
          .replaceAll(RegExp(r'रीफिल कन्फर्म|रीफिल|कन्फर्म'), ' ')
          .replaceAll(RegExp(r'\s+'), ' ')
          .trim();
      if (medQuery.isEmpty) {
        await _speak(_voiceLanguage == 'hi-IN' ? 'कृपया मेडिसिन का नाम बोलें।' : 'Please tell the medicine name.');
        return;
      }
      try {
        final res = await _predictionRepository.confirmRefill(
          medicineName: medQuery,
          quantityUnits: qty,
          confirmationSource: 'voice',
        );
        final uid = (res['order_uid'] ?? '').toString();
        await _speak(
          _voiceLanguage == 'hi-IN'
              ? 'रीफिल ऑर्डर बन गया है ${uid.isNotEmpty ? uid : ''}.'
              : 'Refill order created ${uid.isNotEmpty ? uid : ''}.',
        );
      } catch (_) {
        await _speak(_voiceLanguage == 'hi-IN' ? 'रीफिल कन्फर्म नहीं हो पाया।' : 'Refill confirmation failed.');
      }
      return;
    }

    await _speak(_voiceLanguage == 'hi-IN' ? 'कमांड समझ नहीं आया। हेल्प बोलिए।' : 'Command not recognized. Say help.');
  }

  Future<void> _toggleListening() async {
    if (!_speechReady) {
      await _speak(_voiceLanguage == 'hi-IN' ? 'वॉइस रिकग्निशन उपलब्ध नहीं है।' : 'Voice recognition is not available.');
      return;
    }
    if (_isListening) {
      await _speech.stop();
      if (mounted) setState(() => _isListening = false);
      return;
    }
    await _speech.listen(
      localeId: _speechLocale,
      onResult: (result) async {
        if (result.finalResult) {
          if (mounted) setState(() => _isListening = false);
          await _handleVoiceCommand(result.recognizedWords);
        }
      },
      listenFor: const Duration(seconds: 10),
      pauseFor: const Duration(seconds: 3),
    );
    if (mounted) setState(() => _isListening = true);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _tokenSub?.cancel();
    _onMessageSub?.cancel();
    _onMessageOpenSub?.cancel();
    _notifPoller?.cancel();
    _speech.cancel();
    _audioPlayer.dispose();
    _tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = context.rx;
    return Scaffold(
      body: IndexedStack(index: _i, children: _screens),
      floatingActionButton: _i == 1 ? null : Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
            margin: const EdgeInsets.only(bottom: 8),
            decoration: BoxDecoration(
              color: r.card,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: r.border),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _voiceLanguage,
                dropdownColor: r.card,
                style: TextStyle(color: r.text1, fontSize: 12),
                items: const [
                  DropdownMenuItem(value: 'en-IN', child: Text('EN')),
                  DropdownMenuItem(value: 'hi-IN', child: Text('HI')),
                ],
                onChanged: (v) {
                  if (v != null) _setVoiceLanguage(v);
                },
              ),
            ),
          ),
          FloatingActionButton(
            heroTag: 'voiceAssistantFab',
            backgroundColor: _isListening ? C.err : C.rx,
            onPressed: _toggleListening,
            child: Icon(_isListening ? Icons.mic_off_rounded : Icons.mic_rounded),
          ),
          if (_lastHeard.isNotEmpty)
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              constraints: const BoxConstraints(maxWidth: 220),
              decoration: BoxDecoration(
                color: r.card,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: r.border),
              ),
              child: Text(
                'Heard: $_lastHeard',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: r.text2, fontSize: 11),
              ),
            ),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(color: r.card, border: Border(top: BorderSide(color: r.border, width: 0.5))),
        child: SafeArea(
          top: false,
          child: SizedBox(
            height: 64,
            child: Row(children: [
              _Tab(ic: Icons.home_rounded, lb: 'HOME', on: _i == 0, fn: () => setState(() => _i = 0)),
              _Tab(ic: Icons.chat_bubble_rounded, lb: 'CHAT', on: _i == 1, fn: () => setState(() => _i = 1)),
              _Tab(ic: Icons.medication_rounded, lb: 'MEDS', on: _i == 2, fn: () => setState(() => _i = 2)),
              _Tab(ic: Icons.person_rounded, lb: 'PROFILE', on: _i == 3, fn: () => setState(() => _i = 3)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  final IconData ic;
  final String lb;
  final bool on;
  final VoidCallback fn;
  const _Tab({required this.ic, required this.lb, required this.on, required this.fn});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: fn,
        behavior: HitTestBehavior.opaque,
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            decoration: BoxDecoration(color: on ? C.rx.withOpacity(0.08) : Colors.transparent, borderRadius: BorderRadius.circular(16)),
            child: Icon(ic, size: 20, color: on ? C.rx : context.rx.text3),
          ),
          const SizedBox(height: 3),
          Text(lb, style: GoogleFonts.outfit(fontSize: 9, fontWeight: on ? FontWeight.w700 : FontWeight.w500, color: on ? C.rx : context.rx.text3, letterSpacing: 1.2)),
        ]),
      ),
    );
  }
}
