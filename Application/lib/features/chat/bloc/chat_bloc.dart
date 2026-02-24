import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:dio/dio.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/medicine_model.dart';
import '../../../data/models/order_model.dart';
import '../../../data/repositories/chat_repository.dart';
import '../../../data/repositories/medicine_repository.dart';
import '../../../data/repositories/order_repository.dart';

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

  MedicineModel? _draftMedicine;
  String? _draftDosage;
  int? _draftStrips;
  String? _draftPrescriptionUrl;
  String? _draftPaymentMethod;
  _ChatLang _lang = _ChatLang.hi;
  _ChatStage _stage = _ChatStage.language;

  ChatBloc() : super(const ChatState()) {
    on<LoadChatEvent>(_onLoad);
    on<SendMessageEvent>(_onSend);
    on<ToggleRecordingEvent>(_onToggleRec);
    on<UploadPrescriptionEvent>(_onUploadPrescription);
  }

  void _onLoad(LoadChatEvent event, Emitter<ChatState> emit) {
    emit(
      state.copyWith(
        awaitingLanguage: true,
        languageCode: _lang.code,
        messages: [
          ChatMessage(
            id: '${DateTime.now().millisecondsSinceEpoch}',
            isUser: false,
            text: 'Please choose language:\n1) Hindi\n2) English',
            timestamp: DateTime.now(),
          ),
        ],
      ),
    );
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

    emit(state.copyWith(
      messages: [...state.messages, userMsg],
      isTyping: true,
    ));

    try {
      final responses = await _generateResponses(text);
      emit(
        state.copyWith(
          messages: [...state.messages, ...responses],
          isTyping: false,
          requiresPrescriptionUpload: _stage == _ChatStage.prescription,
          awaitingLanguage: _stage == _ChatStage.language,
          languageCode: _lang.code,
        ),
      );
    } catch (e) {
      final now = DateTime.now();
      emit(
        state.copyWith(
          isTyping: false,
          messages: [
            ...state.messages,
            ChatMessage(
              id: '${now.millisecondsSinceEpoch}',
              isUser: false,
              text: _toReadableError(e),
              timestamp: now,
            ),
          ],
        ),
      );
    }
  }

  void _onToggleRec(ToggleRecordingEvent event, Emitter<ChatState> emit) {
    emit(state.copyWith(isRecording: !state.isRecording));
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
      emit(
        state.copyWith(
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
        ),
      );
    } catch (_) {
      final now = DateTime.now();
      emit(
        state.copyWith(
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
        ),
      );
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

    if (_stage == _ChatStage.selection && _draftMedicine != null) {
      if (l == 'yes' || l == 'y' || l == '1' || l.contains('confirm')) {
        _stage = _ChatStage.dosage;
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: _t(
              hi: 'Great. ${_draftMedicine!.name} ka dosage batao (example: 1 tablet after breakfast).',
              en: 'Great. Share dosage for ${_draftMedicine!.name} (example: 1 tablet after breakfast).',
            ),
            timestamp: now,
          ),
        ];
      }
      _resetDraft();
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
            text: _t(
              hi: 'Theek hai, koi aur medicine ka naam bhejo.',
              en: 'Okay. Please share another medicine name.',
            ),
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.dosage && _draftMedicine != null) {
      _draftDosage = text.trim();
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
    if (results.isEmpty) {
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

    _draftMedicine = results.first;
    _stage = _ChatStage.selection;
    return [
      ChatMessage(
        id: '${now.millisecondsSinceEpoch}',
        isUser: false,
        text: _t(
          hi: 'Kya ye medicine chahiye? "${_draftMedicine!.name}"\n${_draftMedicine!.description ?? "Description not available"}\nReply "yes" to continue.',
          en: 'Is this the correct medicine? "${_draftMedicine!.name}"\n${_draftMedicine!.description ?? "Description not available"}\nReply "yes" to continue.',
        ),
        type: ChatMessageType.meds,
        timestamp: now,
        medicines: results.take(3).toList(),
      ),
    ];
  }

  Future<OrderModel> _placeOrder() async {
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
    );
  }

  void _resetDraft() {
    _draftMedicine = null;
    _draftDosage = null;
    _draftStrips = null;
    _draftPrescriptionUrl = null;
    _draftPaymentMethod = null;
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
