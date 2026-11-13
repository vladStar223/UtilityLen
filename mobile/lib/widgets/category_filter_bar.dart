import 'package:flutter/material.dart';
import '../core/theme.dart';

enum UtilityCategory {
  all('Все', '📊'),
  hws('ХВС', '💧'),
  heating('Отопление', '🔥'),
  dhw('ГВС', '♨️'),
  electricity('Электроэнергия', '⚡');

  final String label;
  final String emoji;
  const UtilityCategory(this.label, this.emoji);
}

class CategoryFilterBar extends StatelessWidget {
  final UtilityCategory selected;
  final ValueChanged<UtilityCategory> onSelected;

  const CategoryFilterBar({
    super.key,
    required this.selected,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        children: UtilityCategory.values.map((cat) {
          final isSelected = cat == selected;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: _FilterChip(
              category: cat,
              isSelected: isSelected,
              onTap: () => onSelected(cat),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final UtilityCategory category;
  final bool isSelected;
  final VoidCallback onTap;

  const _FilterChip({
    required this.category,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          gradient: isSelected
              ? LinearGradient(
                  colors: [
                    AppColors.lavender.withOpacity(0.22),
                    AppColors.violet.withOpacity(0.14),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          color: isSelected ? null : AppColors.glassFill,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: isSelected ? AppColors.lavender.withOpacity(0.55) : AppColors.glassBorder,
            width: isSelected ? 1.5 : 1.0,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: AppColors.violet.withOpacity(0.18),
                    blurRadius: 12,
                    offset: const Offset(0, 3),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              category.emoji,
              style: const TextStyle(fontSize: 14),
            ),
            const SizedBox(width: 6),
            Text(
              category.label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                color: isSelected ? AppColors.lavender : AppColors.textSecondary,
                letterSpacing: 0.1,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
