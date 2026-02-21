import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../../data/models/chat_models.dart';
import '../../../data/models/medicine_model.dart';
import '../../../data/mock_data.dart';

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

// ─── State ───────────────────────────────────────────────
class ChatState extends Equatable {
  final List<ChatMessage> messages;
  final bool isTyping;
  final bool isRecording;

  const ChatState({
    this.messages = const [],
    this.isTyping = false,
    this.isRecording = false,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isTyping,
    bool? isRecording,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        isTyping: isTyping ?? this.isTyping,
        isRecording: isRecording ?? this.isRecording,
      );

  @override
  List<Object?> get props => [messages, isTyping, isRecording];
}

// ─── Bloc ────────────────────────────────────────────────
class ChatBloc extends Bloc<ChatEvent, ChatState> {
  ChatBloc() : super(const ChatState()) {
    on<LoadChatEvent>(_onLoad);
    on<SendMessageEvent>(_onSend);
    on<ToggleRecordingEvent>(_onToggleRec);
  }

  void _onLoad(LoadChatEvent event, Emitter<ChatState> emit) {
    emit(state.copyWith(messages: List.from(MockData.chatInitial)));
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

    await Future.delayed(const Duration(milliseconds: 1500));

    final response = _generateResponse(text);
    emit(state.copyWith(
      messages: [...state.messages, response],
      isTyping: false,
    ));
  }

  void _onToggleRec(ToggleRecordingEvent event, Emitter<ChatState> emit) {
    emit(state.copyWith(isRecording: !state.isRecording));
  }

  ChatMessage _generateResponse(String text) {
    final l = text.toLowerCase();
    final now = DateTime.now();

    if (l.contains('omega') || l.contains('paracetamol') || l.contains('panthenol') || l.contains('panthnol')) {
      final ms = <MedicineModel>[];
      if (l.contains('omega')) ms.add(MockData.medicines.firstWhere((m) => m.name.contains('Omega')));
      if (l.contains('paracetamol')) ms.add(MockData.medicines.firstWhere((m) => m.name.contains('Paracetamol')));
      if (l.contains('panthenol') || l.contains('panthnol')) ms.add(MockData.medicines.firstWhere((m) => m.name.contains('Panthenol')));
      return ChatMessage(
        id: '${now.millisecondsSinceEpoch}',
        isUser: false,
        text: '${ms.length} medicine${ms.length > 1 ? 's' : ''} found:',
        type: ChatMessageType.meds,
        timestamp: now,
        medicines: ms,
      );
    } else if (l.contains('mucosolvan')) {
      return ChatMessage(
        id: '${now.millisecondsSinceEpoch}',
        isUser: false,
        text: 'Found Mucosolvan — safety concern:',
        type: ChatMessageType.safety,
        timestamp: now,
        warnings: const [SafetyWarning(type: 'rx', medicine: 'Mucosolvan 75mg', message: 'Requires valid prescription. Upload to proceed.')],
        medicines: [MockData.medicines.firstWhere((m) => m.name.contains('Mucosolvan'))],
      );
    } else {
      return ChatMessage(
        id: '${now.millisecondsSinceEpoch}',
        isUser: false,
        text: 'Try "I need omega 3 and paracetamol" or "refill panthenol spray".',
        timestamp: now,
      );
    }
  }
}
