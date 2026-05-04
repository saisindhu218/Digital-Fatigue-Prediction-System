import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class QRScreen extends StatefulWidget {
  const QRScreen({super.key});

  @override
  State<QRScreen> createState() => _QRScreenState();
}

class _QRScreenState extends State<QRScreen> {
  bool isScanned = false;

  void _onDetect(Barcode barcode) {
    if (!isScanned) {
      setState(() {
        isScanned = true;
      });

      final String? code = barcode.rawValue;

      if (code != null) {
        _showSuccess();
      }
    }
  }

  void _showSuccess() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("Connected"),
        content: const Text("Device paired successfully!"),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context); // close dialog
              Navigator.pop(context); // go back
            },
            child: const Text("OK"),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Scan QR"),
      ),
      body: MobileScanner(
        onDetect: (barcodeCapture) {
          final List<Barcode> barcodes = barcodeCapture.barcodes;

          if (barcodes.isNotEmpty) {
            _onDetect(barcodes.first);
          }
        },
      ),
    );
  }
}