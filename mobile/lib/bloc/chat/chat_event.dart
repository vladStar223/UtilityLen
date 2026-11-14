import 'package:equatable/equatable.dart';

abstract class ChatEvent extends Equatable {
  const ChatEvent();

  @override
  List<Object?> get props => [];
}

class SendMessageEvent extends ChatEvent {
  final String text;
  final String? comparisonId;
  const SendMessageEvent(this.text, {this.comparisonId});

  @override
  List<Object?> get props => [text, comparisonId];
}

class SelectQuickPromptEvent extends ChatEvent {
  final String prompt;
  final String? comparisonId;
  const SelectQuickPromptEvent(this.prompt, {this.comparisonId});

  @override
  List<Object?> get props => [prompt, comparisonId];
}

class ResetChatEvent extends ChatEvent {}
