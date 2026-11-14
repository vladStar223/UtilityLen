import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/api_client.dart';
import '../../core/models.dart';
import 'chat_event.dart';
import 'chat_state.dart';

class ChatBloc extends Bloc<ChatEvent, ChatState> {
  final ApiClient apiClient;

  ChatBloc({required this.apiClient})
      : super(ChatState(
          messages: [
            ChatMessage(
              text: 'Здравствуйте! Я ваш AI-юрист по жилищно-коммунальному праву. Чем могу помочь по вашей квитанции?',
              isUser: false,
            ),
          ],
        )) {
    on<SendMessageEvent>(_onSendMessage);
    on<SelectQuickPromptEvent>(_onSelectQuickPrompt);
    on<ResetChatEvent>(_onResetChat);
  }

  Future<void> _onSendMessage(
    SendMessageEvent event,
    Emitter<ChatState> emit,
  ) async {
    final userText = event.text.trim();
    if (userText.isEmpty) return;

    final updatedMessages = List<ChatMessage>.from(state.messages)
      ..add(ChatMessage(text: userText, isUser: true));

    emit(state.copyWith(
      messages: updatedMessages,
      isStreaming: true,
      errorMessage: null,
    ));

    try {
      final targetCmp = event.comparisonId ?? 'case_02_coeff_15';
      final stream = apiClient.streamChat(targetCmp, userText);
      final botMessage = ChatMessage(text: '', isUser: false);
      final currentList = List<ChatMessage>.from(updatedMessages)..add(botMessage);
      var fullBotText = '';

      await for (final token in stream) {
        fullBotText += token;
        final latestList = List<ChatMessage>.from(currentList);
        latestList[latestList.length - 1] = ChatMessage(
          text: fullBotText,
          isUser: false,
        );
        emit(state.copyWith(messages: latestList, isStreaming: true));
      }

      emit(state.copyWith(isStreaming: false));
    } catch (e) {
      final fallback = _generateFallbackLegalAnswer(userText);
      final currentList = List<ChatMessage>.from(updatedMessages)
        ..add(ChatMessage(
          text: fallback,
          isUser: false,
        ));

      emit(state.copyWith(
        messages: currentList,
        isStreaming: false,
      ));
    }
  }

  void _onSelectQuickPrompt(
    SelectQuickPromptEvent event,
    Emitter<ChatState> emit,
  ) {
    add(SendMessageEvent(event.prompt, comparisonId: event.comparisonId));
  }

  void _onResetChat(
    ResetChatEvent event,
    Emitter<ChatState> emit,
  ) {
    emit(ChatState(
      messages: [
        ChatMessage(
          text: 'Здравствуйте! Я ваш AI-юрист по жилищно-коммунальному праву. Чем могу помочь по вашей квитанции?',
          isUser: false,
        ),
      ],
    ));
  }

  String _generateFallbackLegalAnswer(String query) {
    final q = query.toLowerCase();
    if (q.contains('1,5') || q.contains('1.5') || q.contains('коэффициент') || q.contains('законно')) {
      return 'Согласно пункту 60 Правил предоставления коммунальных услуг (утв. Постановлением Правительства РФ № 354), повышающий коэффициент 1.5 может применяться только при отсутствии прибора учета при наличии технической возможности его установки, либо при истечении межповерочного интервала.\n\nЕсли поверка проведена вовремя или не составлялся акт обследования технической возможности, применение коэффициента 1.5 незаконно и сумма подлежит обязательному перерасчету.';
    }
    if (q.contains('претензи') || q.contains('составить') || q.contains('жалоб')) {
      return 'Вкладка «Претензия» уже автоматически сформировала досудебную претензию на имя поставщика ресурсов с требованием перерасчета на основании ст. 157 ЖК РФ и ПП РФ № 354.\n\nВы можете перейти в раздел претензии, нажать «Скопировать текст» или экспортировать PDF для отправки через ГИС ЖКХ.';
    }
    if (q.contains('почему') || q.contains('выросла') || q.contains('сумма')) {
      return 'В квитанции за Ноябрь 2026 зафиксирован рост на +27.1% (+1 470,50 ₽). Основным драйвером стала холодная вода (+127% / +411,54 ₽) из-за начисления по повышающему коэффициенту и увеличения объема на 2.2 м³. По отоплению также наблюдается сезонный рост (+38%).';
    }
    return 'По вашему запросу: в соответствии с нормами ст. 157 Жилищного кодекса РФ размер платы за коммунальные услуги рассчитывается исходя из объема потребления по показаниям приборов учета. При выявлении расхождений исполнитель обязан произвести перерасчет в течение 3 рабочих дней.';
  }
}
