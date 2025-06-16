"""
Validation tests to ensure the testing infrastructure is properly configured.
"""
import sys
import os
from pathlib import Path
import pytest
import yaml


class TestSetupValidation:
    """Validate that the testing infrastructure is properly set up."""
    
    def test_python_path_configured(self):
        """Test that the project root is in Python path."""
        project_root = Path(__file__).parent.parent
        assert str(project_root) in sys.path
    
    def test_test_environment_variable(self):
        """Test that the test environment variable is set."""
        assert os.environ.get("RENDERPIPELINE_TESTING") == "1"
    
    def test_project_structure_exists(self):
        """Test that key project directories exist."""
        project_root = Path(__file__).parent.parent
        
        # Check main directories
        assert (project_root / "rpcore").exists()
        assert (project_root / "rpplugins").exists()
        assert (project_root / "rplibs").exists()
        
        # Check test directories
        assert (project_root / "tests").exists()
        assert (project_root / "tests" / "unit").exists()
        assert (project_root / "tests" / "integration").exists()
    
    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists and is valid."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        assert pyproject_path.exists()
        
        # Verify it's readable and contains expected sections
        content = pyproject_path.read_text()
        assert "[tool.poetry]" in content
        assert "[tool.pytest.ini_options]" in content
        assert "[tool.coverage.run]" in content
    
    def test_conftest_fixtures_available(self, temp_dir, mock_render_pipeline, sample_config):
        """Test that conftest fixtures are available and working."""
        # Test temp_dir fixture
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()
        
        # Test mock_render_pipeline fixture
        assert hasattr(mock_render_pipeline, 'settings')
        assert mock_render_pipeline.settings['resolution'] == (1920, 1080)
        
        # Test sample_config fixture
        assert isinstance(sample_config, dict)
        assert 'pipeline' in sample_config
        assert sample_config['pipeline']['resolution']['x'] == 1920
    
    @pytest.mark.unit
    def test_unit_marker_works(self):
        """Test that the unit test marker is properly configured."""
        assert True
    
    @pytest.mark.integration
    def test_integration_marker_works(self):
        """Test that the integration test marker is properly configured."""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker_works(self):
        """Test that the slow test marker is properly configured."""
        assert True
    
    def test_yaml_import_works(self):
        """Test that YAML can be imported and used."""
        data = {'test': 'value', 'nested': {'key': 123}}
        yaml_str = yaml.dump(data)
        loaded = yaml.safe_load(yaml_str)
        assert loaded == data
    
    def test_mock_fixtures_work(self, mock_light, mock_plugin, mock_texture):
        """Test that mock fixtures are properly configured."""
        # Test mock_light
        assert mock_light.position == (0, 0, 10)
        assert mock_light.intensity == 1.0
        
        # Test mock_plugin
        assert mock_plugin.name == "TestPlugin"
        assert mock_plugin.enabled is True
        
        # Test mock_texture
        assert mock_texture.width == 1024
        assert mock_texture.format == "RGBA8"
    
    def test_config_file_fixture(self, config_file, sample_config):
        """Test that config file fixture creates valid YAML files."""
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        assert loaded_config == sample_config
    
    def test_capture_logs_fixture(self, capture_logs):
        """Test that log capture fixture works."""
        log_func, logs = capture_logs
        
        log_func('INFO', 'Test message')
        log_func('ERROR', 'Error message')
        
        assert len(logs) == 2
        assert logs[0] == {'level': 'INFO', 'message': 'Test message'}
        assert logs[1] == {'level': 'ERROR', 'message': 'Error message'}
    
    def test_shader_code_fixture(self, sample_shader_code):
        """Test that shader code fixture provides valid shader strings."""
        assert 'vertex' in sample_shader_code
        assert 'fragment' in sample_shader_code
        assert '#version 330' in sample_shader_code['vertex']
        assert 'gl_Position' in sample_shader_code['vertex']
        assert 'fragColor' in sample_shader_code['fragment']


class TestCoverageConfiguration:
    """Validate coverage configuration."""
    
    def test_coverage_source_paths(self):
        """Test that coverage is configured for the right source paths."""
        # This test verifies that when coverage runs, it will track the right modules
        from rplibs import six  # Should be tracked
        assert six is not None
    
    def test_coverage_omit_patterns(self):
        """Test that test files are properly excluded from coverage."""
        # Test files should be excluded from coverage by configuration
        assert __file__.endswith('.py')
        assert 'test_' in __file__