# 🏢 DealGenie Pro - Commercial Real Estate Analysis Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dealgenie.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Overview

DealGenie Pro is an institutional-grade Commercial Real Estate (CRE) analysis platform that streamlines deal evaluation with OCR-powered data extraction, verified financial calculations, and transparent industry benchmarks.

## ✨ Key Features

### 📸 **Smart Data Input**
- **OCR Technology**: Extract deal data from photos/screenshots
- **Manual Entry**: Traditional form-based input
- **File Upload**: Support for images and documents
- **Confidence Scoring**: OCR accuracy indicators

### 💰 **Financial Analysis**
- **Verified Calculations**:
  - Debt Service Coverage Ratio (DSCR)
  - Mortgage Constant with IO period support
  - Cap Rate analysis
  - Cash-on-Cash returns
  - 5-Year cash flow projections

### 📊 **Transparent Benchmarking**
- **Source Attribution**: Every benchmark cites its source (CBRE, RCA, JLL, etc.)
- **Asset-Specific**: Customized for Office, Multifamily, Industrial, Retail, Hotel
- **Market Adjustments**: Primary/Secondary/Tertiary market variations
- **Real-Time Evaluation**: Instant comparison against industry standards

### 📋 **Due Diligence Management**
- **Asset-Specific Checklists**: Tailored DD items by property type
- **Progress Tracking**: Monitor completion status
- **Risk Flagging**: Automatic identification of critical items

### 📱 **Professional UI/UX**
- **Mobile Responsive**: Optimized for phones and tablets
- **Custom Styling**: Modern gradient design with smooth animations
- **Interactive Charts**: Plotly-powered visualizations
- **Dark Mode Support**: Easy on the eyes

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/dealgenie-app.git
   cd dealgenie-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open in browser**
   ```
   http://localhost:8501
   ```

### Streamlit Cloud Deployment

1. Fork this repository
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy with one click
4. Share your app URL

## 📁 Project Structure

```
dealgenie-app/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Documentation (this file)
├── .gitignore            # Git ignore patterns
├── assets/               # Images and static files
│   └── logo.png         # App logo (if needed)
└── utils/                # Helper modules (optional)
    ├── calculations.py   # Financial calculations
    └── parsers.py       # OCR and data parsing
```

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.streamlit/secrets.toml` file for sensitive data:

```toml
[api_keys]
ocr_api_key = "your-ocr-api-key"
```

### Customization

Modify `BENCHMARKS` dictionary in `app.py` to update industry benchmarks:

```python
BENCHMARKS = {
    "Office": {
        "cap_rate": {"min": 5.5, "preferred": 6.5, "max": 7.5, "source": "CBRE Q4 2024"},
        # ... add more metrics
    }
}
```

## 📊 Technical Highlights

### Financial Accuracy
- **Mortgage Constant**: Verified against industry standard formula
- **DSCR Calculation**: Handles IO periods and varying amortization
- **IRR/NPV**: NumPy-based calculations for accuracy

### Data Validation
- **Input Sanitization**: Prevents invalid data entry
- **Range Checking**: Ensures realistic values
- **Error Handling**: Graceful fallbacks for edge cases

### Performance
- **Caching**: Streamlit's native caching for expensive operations
- **Lazy Loading**: Components load as needed
- **Optimized Charts**: Efficient Plotly configurations

## 🧪 Testing

Run tests (if implemented):
```bash
pytest tests/
```

Key test areas:
- Financial calculation accuracy
- OCR parser reliability
- Benchmark evaluation logic
- UI component rendering

## 📈 Roadmap

- [ ] Real OCR integration with Tesseract
- [ ] PDF report generation
- [ ] Multi-property portfolio analysis
- [ ] API endpoints for external integration
- [ ] Advanced sensitivity analysis
- [ ] Machine learning for deal scoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Data Sources**: CBRE, JLL, RCA, STR, Cushman & Wakefield for benchmark data
- **Libraries**: Streamlit, Plotly, Pandas, NumPy teams
- **Design**: Inter font by Rasmus Andersson

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/dealgenie-app/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dealgenie-app/discussions)
- **Email**: support@dealgenie.pro

## 🔒 Security

For security vulnerabilities, please email security@dealgenie.pro instead of using the issue tracker.

---

**Built with ❤️ for the CRE Community**