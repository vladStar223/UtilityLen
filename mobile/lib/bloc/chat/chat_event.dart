import 'package:equatable/equatable.dart';

abstract class ChatEvent extends Equatable {
  const ChatEvent();

  @override
  List<Object?> get props => [];
}

class SendMessageEvent extends ChatEvent {
  final String text;
  const SendMessageEvent(this.text);

  @override
  List<Object?> get props => [text];
}

class SelectQuickPromptEvent extends ChatEvent {
  final String prompt;
  const SelectQuickPromptEvent(this.prompt);

  @override
  List<Object?> get props => [prompt];
}

class ResetChatEvent extends ChatEvent {}
