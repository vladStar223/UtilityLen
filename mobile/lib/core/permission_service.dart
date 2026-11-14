import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import 'theme.dart';

/// Сервис управления системными разрешениями (Камера, Галерея, Хранилище)
class PermissionService {
  static final ImagePicker _picker = ImagePicker();

  /// Запрос разрешения на доступ к камере
  static Future<bool> requestCameraPermission(BuildContext context) async {
    final status = await Permission.camera.status;
    if (status.isGranted || status.isLimited) {
      return true;
    }

    final result = await Permission.camera.request();
    if (result.isGranted || result.isLimited) {
      return true;
    }

    if (context.mounted) {
      _showPermissionDeniedDialog(
        context: context,
        title: 'Требуется доступ к камере',
        message:
            'Для съемки квитанции ЖКХ приложению UtilityLens необходим доступ к камере устройства.',
        isPermanentlyDenied: result.isPermanentlyDenied,
      );
    }
    return false;
  }

  /// Запрос разрешения на доступ к фотографиям / файловой системе
  static Future<bool> requestStoragePermission(BuildContext context) async {
    // В зависимости от версии Android (13+ использует photos, до 13 - storage)
    PermissionStatus status;
    if (Platform.isAndroid) {
      final photosStatus = await Permission.photos.status;
      if (photosStatus.isGranted || photosStatus.isLimited) {
        return true;
      }
      final storageStatus = await Permission.storage.status;
      if (storageStatus.isGranted || storageStatus.isLimited) {
        return true;
      }

      // Запрашиваем подходящее разрешение
      final requestPhotos = await Permission.photos.request();
      if (requestPhotos.isGranted || requestPhotos.isLimited) {
        return true;
      }
      final requestStorage = await Permission.storage.request();
      if (requestStorage.isGranted || requestStorage.isLimited) {
        return true;
      }
      status = requestPhotos.isPermanentlyDenied || requestStorage.isPermanentlyDenied
          ? PermissionStatus.permanentlyDenied
          : PermissionStatus.denied;
    } else {
      status = await Permission.photos.request();
      if (status.isGranted || status.isLimited) {
        return true;
      }
    }

    if (context.mounted) {
      _showPermissionDeniedDialog(
        context: context,
        title: 'Требуется доступ к галерее',
        message:
            'Для выбора сохраненного фото или скана квитанции приложению необходим доступ к файлам и медиа.',
        isPermanentlyDenied: status.isPermanentlyDenied,
      );
    }
    return false;
  }

  /// Сделать снимок квитанции камерой с проверкой разрешений
  static Future<XFile?> takeReceiptPhoto(BuildContext context) async {
    try {
      final status = await Permission.camera.status;
      if (!status.isGranted && !status.isLimited) {
        final result = await Permission.camera.request();
        if (!result.isGranted && !result.isLimited && context.mounted) {
          // Показываем предупреждение только если перманентно запрещено
          if (result.isPermanentlyDenied) {
            _showPermissionDeniedDialog(
              context: context,
              title: 'Требуется доступ к камере',
              message:
                  'Для съемки квитанции ЖКХ разрешите приложению доступ к камере в настройках.',
              isPermanentlyDenied: true,
            );
          }
        }
      }

      final picked = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1600,
        maxHeight: 2048,
        imageQuality: 85,
      );
      return picked;
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Ошибка съемки: $e'),
            backgroundColor: AppColors.critical,
          ),
        );
      }
      return null;
    }
  }

  /// Выбрать изображение квитанции из галереи (Photo Picker не требует runtime-прав на Android 13+)
  static Future<XFile?> pickReceiptFromGallery(BuildContext context) async {
    try {
      final picked = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1600,
        maxHeight: 2048,
        imageQuality: 85,
      );
      return picked;
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Ошибка доступа к файлам: $e'),
            backgroundColor: AppColors.critical,
          ),
        );
      }
      return null;
    }
  }

  /// Диалог с пояснением, зачем нужно разрешение, и кнопкой перехода в настройки
  static void _showPermissionDeniedDialog({
    required BuildContext context,
    required String title,
    required String message,
    required bool isPermanentlyDenied,
  }) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(
          title,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        content: Text(
          isPermanentlyDenied
              ? '$message\n\nРазрешение было отключено ранее. Пожалуйста, включите его в системных настройках приложения.'
              : message,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 14,
            height: 1.4,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text(
              'Отмена',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ),
          if (isPermanentlyDenied)
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                openAppSettings();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              child: const Text('Настройки'),
            )
          else
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              child: const Text('Понятно'),
            ),
        ],
      ),
    );
  }
}
