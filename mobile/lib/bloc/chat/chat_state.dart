import 'package:equatable/equatable.dart';
import '../../core/models.dart';

class ChatState extends Equatable {
  final List<ChatMessage> messages;
  final bool isStreaming;
  final String? errorMessage;
  final List<String> quickPrompts;

  const ChatState({
    required this.messages,
    this.isStreaming = false,
    this.errorMessage,
    this.quickPrompts = const [
      'Законно ли начисление 1,5?',
      'Почему выросла сумма?',
      'Составить претензию в УК',
      'Как оспорить переплату?',
    ],
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isStreaming,
    String? errorMessage,
    List<String>? quickPrompts,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isStreaming: isStreaming ?? this.isStreaming,
      errorMessage: errorMessage ?? this.errorMessage,
      quickPrompts: quickPrompts ?? this.quickPrompts,
    );
  }

  @override
  List<Object?> get props => [messages, isStreaming, errorMessage, quickPrompts];
}
