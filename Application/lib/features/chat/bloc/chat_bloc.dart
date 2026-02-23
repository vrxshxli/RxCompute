import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/medicine_model.dart';
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

  const ChatState({
    this.messages = const [],
    this.isTyping = false,
    this.isRecording = false,
    this.requiresPrescriptionUpload = false,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isTyping,
    bool? isRecording,
    bool? requiresPrescriptionUpload,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        isTyping: isTyping ?? this.isTyping,
        isRecording: isRecording ?? this.isRecording,
        requiresPrescriptionUpload: requiresPrescriptionUpload ?? this.requiresPrescriptionUpload,
      );

  @override
  List<Object?> get props => [messages, isTyping, isRecording, requiresPrescriptionUpload];
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
  _ChatStage _stage = _ChatStage.idle;

  ChatBloc() : super(const ChatState()) {
    on<LoadChatEvent>(_onLoad);
    on<SendMessageEvent>(_onSend);
    on<ToggleRecordingEvent>(_onToggleRec);
    on<UploadPrescriptionEvent>(_onUploadPrescription);
  }

  void _onLoad(LoadChatEvent event, Emitter<ChatState> emit) {
    emit(
      state.copyWith(
        messages: [
          ChatMessage(
            id: '${DateTime.now().millisecondsSinceEpoch}',
            isUser: false,
            text:
                "Hello! Aap medicine ka naam bhejo. Main confirm karke dosage aur strips poochunga, phir order place kar dunga.",
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

    final responses = await _generateResponses(text);
    emit(
      state.copyWith(
        messages: [...state.messages, ...responses],
        isTyping: false,
        requiresPrescriptionUpload: _stage == _ChatStage.prescription,
      ),
    );
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
      _stage = _ChatStage.confirm;
      final now = DateTime.now();
      emit(
        state.copyWith(
          isTyping: false,
          requiresPrescriptionUpload: false,
          messages: [
            ...state.messages,
            ChatMessage(
              id: '${now.millisecondsSinceEpoch}',
              isUser: false,
              text: 'Prescription upload ho gaya. Ab order confirm karne ke liye "yes" bhejo.',
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

    if (_stage == _ChatStage.selection && _draftMedicine != null) {
      if (l == 'yes' || l == 'y' || l == '1' || l.contains('confirm')) {
        _stage = _ChatStage.dosage;
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: 'Great. ${_draftMedicine!.name} ka dosage batao (example: 1 tablet after breakfast).',
            timestamp: now,
          ),
        ];
      }
      _resetDraft();
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: 'Theek hai, koi aur medicine ka naam bhejo.',
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
          text: 'Kitni strips/chhote packs chahiye ${_draftMedicine!.name} ki?',
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
            text: 'Please valid number bhejo. Example: 2',
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

      _stage = _ChatStage.confirm;
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text:
              'Confirm karo: ${_draftMedicine!.name}, dosage "${_draftDosage ?? '-'}", strips ${_draftStrips ?? 1}. Reply "yes" to place order.',
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.prescription) {
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: 'Prescription upload karo, fir main order confirm karwaunga.',
          timestamp: now,
        ),
      ];
    }

    if (_stage == _ChatStage.confirm && _draftMedicine != null && _draftStrips != null) {
      if (l != 'yes' && l != 'y' && !l.contains('confirm')) {
        _resetDraft();
        return [
          ChatMessage(
            id: '${now.millisecondsSinceEpoch}',
            isUser: false,
            text: 'Order cancel ho gaya. New medicine bhej kar dobara start kar sakte ho.',
            timestamp: now,
          ),
        ];
      }

      final order = await _orderRepo.createOrder(
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
      );
      _resetDraft();
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: 'Order placed successfully.',
          type: ChatMessageType.confirmed,
          timestamp: now,
          order: order,
        ),
      ];
    }

    final results = await _medicineRepo.getMedicines(search: text.trim());
    if (results.isEmpty) {
      return [
        ChatMessage(
          id: '${now.millisecondsSinceEpoch}',
          isUser: false,
          text: 'Medicine nahi mili. Name ya PZN ke saath try karo.',
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
        text:
            'Kya ye medicine chahiye? "${_draftMedicine!.name}"\n${_draftMedicine!.description ?? "Description not available"}\nReply "yes" to continue.',
        type: ChatMessageType.meds,
        timestamp: now,
        medicines: results.take(3).toList(),
      ),
    ];
  }

  void _resetDraft() {
    _draftMedicine = null;
    _draftDosage = null;
    _draftStrips = null;
    _draftPrescriptionUrl = null;
    _stage = _ChatStage.idle;
  }
}

enum _ChatStage {
  idle,
  selection,
  dosage,
  strips,
  prescription,
  confirm,
}
