import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/medicine_model.dart';
import '../../../data/models/order_model.dart';
import '../../../data/repositories/chat_repository.dart';
import '../../../data/repositories/medicine_repository.dart';
import '../../../data/repositories/order_repository.dart';
import '../../../data/repositories/user_repository.dart';

// ─── Events ──────────────────────────────────────────────
abstract class ChatEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class LoadChatEvent extends ChatEvent {}

class SendMessageEvent extends ChatEvent {
  final String text;
  SendMessageEvent(this.text);

  @override
  List<Object?> get props => [text];
}

class ToggleRecordingEvent extends ChatEvent {}

class UploadPrescriptionEvent extends ChatEvent {
  final String filePath;
  UploadPrescriptionEvent(this.filePath);

  @override
  List<Object?> get props => [filePath];
}

class UpdateDraftStripsEvent extends ChatEvent {
  final int strips;
  UpdateDraftStripsEvent(this.strips);

  @override
  List<Object?> get props => [strips];
}

class SelectMedicineEvent extends ChatEvent {
  final MedicineModel medicine;
  SelectMedicineEvent(this.medicine);

  @override
  List<Object?> get props => [medicine.id];
}

// ─── State ───────────────────────────────────────────────
class ChatState extends Equatable {
  final List<ChatMessage> messages;
  final bool isTyping;
  final bool isRecording;
  final bool requiresPrescriptionUpload;
  final bool awaitingLanguage;
  final String languageCode;

  const ChatState({
    this.messages = const [],
    this.isTyping = false,
    this.isRecording = false,
    this.requiresPrescriptionUpload = false,
    this.awaitingLanguage = true,
    this.languageCode = 'hi',
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isTyping,
    bool? isRecording,
    bool? requiresPrescriptionUpload,
    bool? awaitingLanguage,
    String? languageCode,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        isTyping: isTyping ?? this.isTyping,
        isRecording: isRecording ?? this.isRecording,
        requiresPrescriptionUpload: requiresPrescriptionUpload ?? this.requiresPrescriptionUpload,
        awaitingLanguage: awaitingLanguage ?? this.awaitingLanguage,
        languageCode: languageCode ?? this.languageCode,
      );

  @override
  List<Object?> get props => [messages, isTyping, isRecording, requiresPrescriptionUpload, awaitingLanguage, languageCode];
}

// ─── Bloc ────────────────────────────────────────────────
class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final MedicineRepository _medicineRepo = MedicineRepository();
  final OrderRepository _orderRepo = OrderRepository();
  final ChatRepository _chatRepo = ChatRepository();
  final UserRepository _userRepo = UserRepository();

  static const String _chatMessagesKey = 'chat_messages_v1';
  static const String _chatLangKey = 'chat_language_v1';
  static const String _chatAliasesKey = 'chat_medicine_aliases_v1';

  MedicineModel? _draftMedicine;
  String? _draftDosage;
  int? _draftStrips;
  String? _draftPrescriptionUrl;
  String? _draftPaymentMethod;
  bool _stripsSelectedByUser = false;
  String? _lastSearchQuery;
  List<MedicineModel> _candidateMedicines = const [];
  _ChatLang _lang = _ChatLang.hi;
  _ChatStage _stage = _ChatStage.language;

  ChatBloc() : super(const ChatState()) {
    on<LoadChatEvent>(_onLoad);
    on<SendMessageEvent>(_onSend);
    on<ToggleRecordingEvent>(_onToggleRec);
    on<UploadPrescriptionEvent>(_onUploadPrescription);
    on<UpdateDraftStripsEvent>(_onUpdateDraftStrips);
    on<SelectMedicineEvent>(_onSelectMedicine);
  }

  Future<void> _onLoad(LoadChatEvent event, Emitter<ChatState> emit) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList(_chatMessagesKey) ?? [];
    final langCode = prefs.getString(_chatLangKey);
    if (langCode == 'en') _lang = _ChatLang.en;

    if (saved.isNotEmpty) {
      final restored = saved.map(_decodeMessage).whereType<ChatMessage>().toList();
      if (restored.isEmpty) {
        final initial = [
          ChatMessage(
            id: '${DateTime.now().millisecondsSinceEpoch}',
            isUser: false,
            text: 'Please choose language:\n1) Hindi\n2) English',
            timestamp: DateTime.now(),
          ),
        ];
        emit(
          state.copyWith(
            awaitingLanguage: true,
            languageCode: _lang.code,
            messages: initial,
          ),
        );
        await _persistChat(initial);
        return;
      }
      emit(
        state.copyWith(
          awaitingLanguage: false,
          languageCode: _lang.code,
          messages: restored,
        ),
      );
      return;
    }

    final initial = [
      ChatMessage(
        id: '${DateTime.now().millisecondsSinceEpoch}',
        isUser: false,
        text: 'Please choose language:\n1) Hindi\n2) English',
        timestamp: DateTime.now(),
      ),
    ];
    emit(
      state.copyWith(
        awaitingLanguage: true,
        languageCode: _lang.code,
        messages: initial,
      ),
    );
    await _persistChat(initial);
  }

  Future<void> _onSend(SendMessageEvent event, Emitter<ChatState> emit) async {
    final text = event.text.trim();
    if (text.isEmpty) return;

    final userMsg = ChatMessage(
      id: '${DateTime.now().millisecondsSinceEpoch}',
      isUser: true,
      text: text,
      timestamp: DateTime.now(),
    );

    final staged = state.copyWith(
      messages: [...state.messages, userMsg],
      isTyping: true,
    );
    emit(staged);
    await _persistChat(staged.messages);

    try {
      final responses = await _generateResponses(text);
      final next = state.copyWith(
          messages: [...staged.messages, ...responses],
          isTyping: false,
          requiresPrescriptionUpload: _stage == _ChatStage.prescription,
          awaitingLanguage: _stage == _ChatStage.language,
          languageCode: _lang.code,
        );
      emit(next);
      await _persistChat(next.messages);
    } catch (e) {
      final now = DateTime.now();
      final failed = state.copyWith(
          isTyping: false,
          messages: [
            ...staged.messages,
            ChatMessage(
              id: '${now.millisecondsSinceEpoch}',
              isUser: false,
              text: _toReadableError(e),
              timestamp: now,
            ),
          ],
        );
      emit(failed);
      await _persistChat(failed.messages);
    }
  }

  void _onToggleRec(ToggleRecordingEvent event, Emitter<ChatState> emit) {
    emit(state.copyWith(isRecording: !state.isRecording));
  }

  void _onUpdateDraftStrips(UpdateDraftStripsEvent event, Emitter<ChatState> emit) {
    if (event.strips > 0) {
      _draftStrips = event.strips;
      _stripsSelectedByUser = true;
    }
  }

  Future<void> _onSelectMedicine(SelectMedicineEvent event, Emitter<ChatState> emit) async {
    _draftMedicine = _withPredictedRx([event.medicine]).first;
    _draftStrips = null;
    _stripsSelectedByUser = false;
    _stage = _ChatStage.dosage;
    if (_lastSearchQuery != null && _lastSearchQuery!.isNotEmpty) {
      await _saveAlias(_lastSearchQuery!, _draftMedicine!.id);
    }
    final now = DateTime.now();
    final next = state.copyWith(
      messages: [
        ...state.messages,
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: true,
          text: _draftMedicine!.name,
          timestamp: now,
        ),
        ChatMessage(
          id: '${now.millisecondsSinceEpoch + 1}',
          isUser: false,
          text: _t(
            hi: 'Selected: ${_draftMedicine!.name}. Ab dosage batao.',
            en: 'Selected: ${_draftMedicine!.name}. Now share dosage.',
          ),
          timestamp: DateTime.now(),
        ),
      ],
      awaitingLanguage: false,
      languageCode: _lang.code,
    );
    emit(next);
    await _persistChat(next.messages);
  }

  Future<void> _onUploadPrescription(
    UploadPrescriptionEvent event,
    Emitter<ChatState> emit,
  ) async {
    emit(state.copyWith(isTyping: true));
    try {
      final url = await _chatRepo.uploadPrescription(event.filePath);
      _draftPrescriptionUrl = url;
      _stage = _ChatStage.payment;
      final now = DateTime.now();
      final next = state.copyWith(
          isTyping: false,
          requiresPrescriptionUpload: false,
          awaitingLanguage: _stage == _ChatStage.language,
          languageCode: _lang.code,
          messages: [
            ...state.messages,
            ChatMessage(
              id: '${now.millisecondsSinceEpoch}',
              isUser: false,
              text: _t(
                hi: 'Prescription upload ho gaya. Ab payment method batao: COD ya ONLINE.',
                en: 'Prescription uploaded. Please choose payment method: COD or ONLINE.',
              ),
              timestamp: now,
            ),
          ],
        );
      emit(next);
      await _persistChat(next.messages);
    } catch (_) {
      final now = DateTime.now();
      final failed = state.copyWith(
          isTyping: false,
          messages: [
            ...state.messages,
            ChatMessage(
              id: '${now.millisecondsSinceEpoch}',
              isUser: false,
              text: 'Prescription upload failed. Please try again.',
              timestamp: now,
            ),
          ],
        );
      emit(failed);
      await _persistChat(failed.messages);
    }
  }

  Future<List<ChatMessage>> _generateResponses(String text) async {
    await Future.delayed(const Duration(milliseconds: 700));
    final l = text.toLowerCase().trim();
    final now = DateTime.now();

    if (_stage == _ChatStage.language) {
      if (l == '1' || l.contains('hindi') || l == 'hi') {
        _lang = _ChatLang.hi;
        _stage = _ChatStage.idle;
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: 'Language set: Hindi. Ab medicine ka naam bhejo.',
            timestamp: now,
          ),
        ];
      }
      if (l == '2' || l.contains('english') || l == 'en') {
        _lang = _ChatLang.en;
        _stage = _ChatStage.idle;
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: 'Language set: English. Please type medicine name.',
            timestamp: now,
          ),
        ];
      }
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: 'Please select language first: 1 for Hindi, 2 for English.',
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.selection && _candidateMedicines.isNotEmpty) {
      final selected = _selectFromCandidates(l);
      if (selected != null) {
        _draftMedicine = selected;
        _draftStrips = null;
        _stripsSelectedByUser = false;
        _stage = _ChatStage.dosage;
        if (_lastSearchQuery != null && _lastSearchQuery!.isNotEmpty) {
          await _saveAlias(_lastSearchQuery!, selected.id);
        }
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: _t(
              hi: 'Selected: ${selected.name}. Ab dosage batao.',
              en: 'Selected: ${selected.name}. Now share dosage.',
            ),
            timestamp: now,
          ),
        ];
      }
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Please option number select karo ya Select button dabao.',
            en: 'Please choose an option number or tap Select button.',
          ),
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.dosage && _draftMedicine != null) {
      _draftDosage = text.trim();
      if (_stripsSelectedByUser && (_draftStrips ?? 0) > 0) {
        if (_draftMedicine!.rxRequired && (_draftPrescriptionUrl == null || _draftPrescriptionUrl!.isEmpty)) {
          _stage = _ChatStage.prescription;
          return [
            ChatMessage(
              id: '${now.millisecondsSinceEpoch}',
              isUser: false,
              text: '${_draftMedicine!.name} ke liye prescription required hai.',
              type: ChatMessageType.safety,
              timestamp: now,
              warnings: [
                const SafetyWarning(
                  type: 'rx',
                  medicine: 'Prescription Required',
                  message: 'Upload Prescription button se file upload karein.',
                ),
              ],
              medicines: [_draftMedicine!],
            ),
          ];
        }
        _stage = _ChatStage.payment;
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: _t(
              hi: 'Payment method choose karo: COD ya ONLINE.',
              en: 'Please choose payment method: COD or ONLINE.',
            ),
            timestamp: now,
          ),
        ];
      }
      _stage = _ChatStage.strips;
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Kitni strips/chhote packs chahiye ${_draftMedicine!.name} ki?',
            en: 'How many strips/packs do you need for ${_draftMedicine!.name}?',
          ),
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.strips && _draftMedicine != null) {
      final strips = int.tryParse(l);
      if (strips == null || strips <= 0) {
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: _t(
              hi: 'Please valid number bhejo. Example: 2',
              en: 'Please send a valid number. Example: 2',
            ),
            timestamp: now,
          ),
        ];
      }
      _draftStrips = strips;

      if (_draftMedicine!.rxRequired && (_draftPrescriptionUrl == null || _draftPrescriptionUrl!.isEmpty)) {
        _stage = _ChatStage.prescription;
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: '${_draftMedicine!.name} ke liye prescription required hai.',
            type: ChatMessageType.safety,
            timestamp: now,
            warnings: [
              const SafetyWarning(
                type: 'rx',
                medicine: 'Prescription Required',
                message: 'Upload Prescription button se file upload karein.',
              ),
            ],
            medicines: [_draftMedicine!],
          ),
        ];
      }

      _stage = _ChatStage.payment;
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Payment method choose karo: COD ya ONLINE.',
            en: 'Please choose payment method: COD or ONLINE.',
          ),
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.prescription) {
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Prescription upload karo, fir payment method choose karenge.',
            en: 'Upload prescription, then we will select payment method.',
          ),
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.payment && _draftMedicine != null && _draftStrips != null) {
      if (l.contains('cod') || l.contains('cash')) {
        _draftPaymentMethod = 'cod';
        final order = await _placeOrder();
        _resetDraft();
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: _t(
              hi: 'COD select hua. Order place ho gaya.',
              en: 'COD selected. Order placed successfully.',
            ),
            type: ChatMessageType.confirmed,
            timestamp: now,
            order: order,
          ),
        ];
      }

      if (l.contains('online') || l.contains('upi') || l.contains('card') || l.contains('gpay') || l.contains('pay')) {
        _draftPaymentMethod = 'online';
        final processing = ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Online payment processing (mock)...',
            en: 'Processing online payment (mock)...',
          ),
          timestamp: now,
        );
        await Future.delayed(const Duration(milliseconds: 900));
        final order = await _placeOrder();
        _resetDraft();
        return [
          processing,
          ChatMessage(
            id: '${now.millisecondsSinceEpoch + 1}',
            isUser: false,
            text: _t(
              hi: 'Mock payment successful. Order placed.',
              en: 'Mock payment successful. Order placed.',
            ),
            type: ChatMessageType.confirmed,
            timestamp: DateTime.now(),
            order: order,
          ),
        ];
      }

      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Please payment method likho: COD ya ONLINE.',
            en: 'Please type payment method: COD or ONLINE.',
          ),
          timestamp: now,
        ),
      ];
    }

    final results = await _medicineRepo.getMedicines(search: text.trim());
    _lastSearchQuery = text.trim();
    if (results.isEmpty) {
      final suggestions = _withPredictedRx(await _suggestMedicines(text.trim()));
      if (suggestions.isNotEmpty) {
        _candidateMedicines = suggestions;
        _stage = _ChatStage.selection;
        final names = suggestions.map((m) => m.name).join('\n- ');
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: _t(
              hi: 'Exact medicine nahi mili. Kya aap inme se koi chahte ho?\n- $names',
              en: 'Exact medicine not found. Did you mean one of these?\n- $names',
            ),
            type: ChatMessageType.options,
            timestamp: now,
            medicines: suggestions,
          ),
        ];
      }
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: _t(
            hi: 'Medicine nahi mili. Name ya PZN ke saath try karo.',
            en: 'Medicine not found. Try with name or PZN.',
          ),
          timestamp: now,
        ),
      ];
    }

    final predicted = _withPredictedRx(results);
    _candidateMedicines = predicted.take(5).toList();
    _draftMedicine = _candidateMedicines.first;
    _stage = _ChatStage.selection;
    return [
      ChatMessage(
        id: '${now.millisecondsSinceEpoch}',
        isUser: false,
        text: _t(
          hi: 'Related medicines list ye hai. Neeche se correct medicine select karo.',
          en: 'Here are related medicines. Select the correct medicine from the list below.',
        ),
        type: ChatMessageType.options,
        timestamp: now,
        medicines: _candidateMedicines,
      ),
    ];
  }

  Future<OrderModel> _placeOrder() async {
    String? deliveryAddress;
    double? deliveryLat;
    double? deliveryLng;
    try {
      final profile = await _userRepo.getProfile();
      deliveryAddress = profile.locationText;
      deliveryLat = profile.locationLat;
      deliveryLng = profile.locationLng;
    } catch (_) {}
    return _orderRepo.createOrder(
      items: [
        {
          'medicine_id': _draftMedicine!.id,
          'name': _draftMedicine!.name,
          'quantity': _draftStrips,
          'price': _draftMedicine!.price,
          'dosage_instruction': _draftDosage,
          'strips_count': _draftStrips,
          if (_draftPrescriptionUrl != null) 'prescription_file': _draftPrescriptionUrl,
        },
      ],
      paymentMethod: _draftPaymentMethod,
      deliveryAddress: deliveryAddress,
      deliveryLat: deliveryLat,
      deliveryLng: deliveryLng,
    );
  }

  void _resetDraft() {
    _draftMedicine = null;
    _draftDosage = null;
    _draftStrips = null;
      _stripsSelectedByUser = false;
    _draftPrescriptionUrl = null;
    _draftPaymentMethod = null;
    _candidateMedicines = const [];
    _lastSearchQuery = null;
    _stage = _ChatStage.idle;
  }

  String _t({required String hi, required String en}) => _lang == _ChatLang.hi ? hi : en;

  String _toReadableError(Object error) {
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map && data['detail'] is Map) {
        final detail = data['detail'] as Map;
        final message = detail['message'];
        if (message is String && message.trim().isNotEmpty) return message;
      }
      if (data is Map && data['detail'] is String) {
        return data['detail'] as String;
      }
      if (error.message != null && error.message!.trim().isNotEmpty) {
        return error.message!;
      }
    }
    return 'Order place nahi ho paaya. Please ek baar phir try karo.';
  }

  Future<void> _persistChat(List<ChatMessage> messages) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_chatLangKey, _lang.code);
    await prefs.setStringList(_chatMessagesKey, messages.map(_encodeMessage).toList());
  }

  String _encodeMessage(ChatMessage m) {
    final meds = (m.medicines ?? [])
        .map((e) => [e.id, e.name, e.pzn, e.price, e.package, e.stock, e.rxRequired, e.description, e.imageUrl, e.quantity].join('~'))
        .join('|');
    final order = m.order == null ? '' : '${m.order!.id}~${m.order!.orderUid}~${m.order!.userId}~${m.order!.status.name}~${m.order!.total}~${m.order!.createdAt.toIso8601String()}';
    return [
      m.id,
      m.isUser ? '1' : '0',
      m.type.name,
      m.timestamp.toIso8601String(),
      m.text.replaceAll('\n', '\\n'),
      meds,
      order,
    ].join('::');
  }

  ChatMessage? _decodeMessage(String raw) {
    try {
      final parts = raw.split('::');
      if (parts.length < 5) return null;
      final medsRaw = parts.length > 5 ? parts[5] : '';
      final orderRaw = parts.length > 6 ? parts[6] : '';
      final meds = medsRaw.isEmpty
          ? null
          : medsRaw.split('|').map((item) {
              final p = item.split('~');
              return MedicineModel(
                id: int.parse(p[0]),
                name: p[1],
                pzn: p[2],
                price: double.parse(p[3]),
                package: p[4].isEmpty ? null : p[4],
                stock: int.parse(p[5]),
                rxRequired: p[6] == 'true',
                description: p[7].isEmpty ? null : p[7],
                imageUrl: p[8].isEmpty ? null : p[8],
                quantity: int.parse(p[9]),
              );
            }).toList();

      OrderModel? order;
      if (orderRaw.isNotEmpty) {
        final p = orderRaw.split('~');
        order = OrderModel(
          id: int.parse(p[0]),
          orderUid: p[1],
          userId: int.parse(p[2]),
          status: OrderStatus.fromString(p[3]),
          total: double.parse(p[4]),
          createdAt: DateTime.parse(p[5]),
        );
      }

      return ChatMessage(
        id: parts[0],
        isUser: parts[1] == '1',
        type: ChatMessageType.values.firstWhere((e) => e.name == parts[2], orElse: () => ChatMessageType.text),
        timestamp: DateTime.parse(parts[3]),
        text: parts[4].replaceAll('\\n', '\n'),
        medicines: meds,
        order: order,
      );
    } catch (_) {
      return null;
    }
  }

  Future<List<MedicineModel>> _suggestMedicines(String query) async {
    final aliasMap = await _loadAliases();
    final normalizedQuery = _normalizeQuery(query);
    if (aliasMap.containsKey(normalizedQuery)) {
      final all = await _medicineRepo.getMedicines();
      final mapped = all.where((m) => m.id == aliasMap[normalizedQuery]).toList();
      if (mapped.isNotEmpty) return mapped;
    }

    final all = await _medicineRepo.getMedicines();
    if (all.isEmpty) return const [];
    final q = query.toLowerCase().trim();
    final ranked = all.map((m) {
      final name = m.name.toLowerCase();
      final dist = _levenshtein(name, q);
      final maxLen = name.length > q.length ? name.length : q.length;
      final score = maxLen == 0 ? 0 : (1 - (dist / maxLen));
      final bonus = name.contains(q) ? 0.25 : 0.0;
      return (med: m, score: score + bonus);
    }).toList()
      ..sort((a, b) => b.score.compareTo(a.score));
    return ranked.take(3).map((e) => e.med).toList();
  }

  MedicineModel? _selectFromCandidates(String input) {
    if (_candidateMedicines.isEmpty) return null;
    final idx = int.tryParse(input);
    if (idx != null && idx >= 1 && idx <= _candidateMedicines.length) {
      return _candidateMedicines[idx - 1];
    }

    for (final med in _candidateMedicines) {
      final name = med.name.toLowerCase();
      if (input == name || name.contains(input) || input.contains(name)) {
        return med;
      }
    }
    return null;
  }

  List<MedicineModel> _withPredictedRx(List<MedicineModel> meds) {
    return meds.map((m) {
      final predicted = m.rxRequired || _predictRxByName(m.name);
      if (predicted == m.rxRequired) return m;
      return MedicineModel(
        id: m.id,
        name: m.name,
        pzn: m.pzn,
        price: m.price,
        package: m.package,
        stock: m.stock,
        rxRequired: predicted,
        description: m.description,
        imageUrl: m.imageUrl,
        quantity: m.quantity,
      );
    }).toList();
  }

  bool _predictRxByName(String name) {
    final n = name.toLowerCase();
    const rxHints = [
      'ramipril',
      'atorvastatin',
      'amoxicillin',
      'metformin',
      'mucosolvan',
      'colpofix',
      'minoxidil',
      'femiloges',
      'retardkapseln',
    ];
    return rxHints.any((k) => n.contains(k));
  }

  int _levenshtein(String s, String t) {
    final m = s.length;
    final n = t.length;
    if (m == 0) return n;
    if (n == 0) return m;
    final d = List.generate(m + 1, (_) => List<int>.filled(n + 1, 0));
    for (var i = 0; i <= m; i++) {
      d[i][0] = i;
    }
    for (var j = 0; j <= n; j++) {
      d[0][j] = j;
    }
    for (var i = 1; i <= m; i++) {
      for (var j = 1; j <= n; j++) {
        final cost = s[i - 1] == t[j - 1] ? 0 : 1;
        d[i][j] = [
          d[i - 1][j] + 1,
          d[i][j - 1] + 1,
          d[i - 1][j - 1] + cost,
        ].reduce((a, b) => a < b ? a : b);
      }
    }
    return d[m][n];
  }

  Future<Map<String, int>> _loadAliases() async {
    final prefs = await SharedPreferences.getInstance();
    final rows = prefs.getStringList(_chatAliasesKey) ?? [];
    final out = <String, int>{};
    for (final row in rows) {
      final parts = row.split('::');
      if (parts.length != 2) continue;
      final id = int.tryParse(parts[1]);
      if (id == null) continue;
      out[parts[0]] = id;
    }
    return out;
  }

  Future<void> _saveAlias(String query, int medicineId) async {
    final prefs = await SharedPreferences.getInstance();
    final map = await _loadAliases();
    map[_normalizeQuery(query)] = medicineId;
    final rows = map.entries.map((e) => '${e.key}::${e.value}').toList();
    await prefs.setStringList(_chatAliasesKey, rows);
  }

  String _normalizeQuery(String q) {
    return q.toLowerCase().replaceAll(RegExp(r'[^a-z0-9\s]'), ' ').replaceAll(RegExp(r'\s+'), ' ').trim();
  }
}

enum _ChatStage {
  language,
  idle,
  selection,
  dosage,
  strips,
  prescription,
  payment,
}

enum _ChatLang {
  hi,
  en;

  String get code => this == _ChatLang.hi ? 'hi' : 'en';
}
