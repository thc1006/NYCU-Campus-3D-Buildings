# Contributing to NQSD

Thank you for your interest in contributing to the NYCU Campus Building Spatial Dataset project!

## 📋 Ways to Contribute

### 1. Report Issues
- **Data Errors**: Found incorrect building heights, coordinates, or attributes?
- **Documentation**: Spotted typos or unclear instructions?
- **Code Bugs**: Encountered errors when running scripts?

Please use our [issue templates](.github/ISSUE_TEMPLATE/) to report.

### 2. Submit Pull Requests
- **Data Updates**: New building data, updated floor plans
- **Script Improvements**: Bug fixes, new features, performance optimization
- **Documentation**: Clarifications, examples, translations

### 3. Share Use Cases
- Published research using this dataset? We'd love to hear about it!
- Created visualization or analysis? Share your work!

## 🔄 Development Workflow

### Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/NQSD.git
cd NQSD

# Install dependencies
pip install -r scripts/requirements.txt

# Download raw data from GitHub Release
# (See README.md for instructions)
```

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow existing code style
   - Update documentation if needed
   - Test your changes

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation changes
   - `refactor:` Code refactoring
   - `test:` Test additions or changes
   - `chore:` Maintenance tasks

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## 📝 Code Guidelines

### Python Scripts
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Include type hints where appropriate
- Keep functions focused and modular

### Data Files
- Use UTF-8 encoding
- Follow existing naming conventions
- Include metadata.json when adding new data
- Document data sources and processing steps

### Documentation
- Use clear, concise language
- Include examples where helpful
- Keep README files up to date
- Add comments for complex code

## 🧪 Testing

Before submitting a PR:
```bash
# Test data processing scripts
python scripts/01_download_nlsc_tiles.py --test
python scripts/02_extract_osm_buildings.py --test
python scripts/03_parse_nlsc_tiles.py --test
python scripts/04_merge_datasets.py --test

# Validate output data
python scripts/utils/validate_organization.py
```

## 📊 Data Quality Standards

When contributing data:
- Verify coordinates are in correct CRS (TWD97 or WGS84)
- Ensure building heights are in meters
- Include data source and collection date
- Follow attribute naming conventions
- Provide sample data for testing

## 🔍 Review Process

1. Automated checks run on all PRs
2. Maintainers review code and documentation
3. Community feedback is encouraged
4. Approved PRs are merged to main branch

## 📞 Questions?

- Open a [Discussion](https://github.com/YOUR_USERNAME/NQSD/discussions)
- Contact maintainers via email
- Check existing issues and PRs first

## 📜 License

By contributing, you agree that your contributions will be licensed under the CC BY 4.0 License.

Thank you for helping improve NQSD! 🎉
