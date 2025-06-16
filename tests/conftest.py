"""
Shared pytest fixtures and configuration for RenderPipeline tests.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest
import yaml


@pytest.fixture
def temp_dir():
    """Create a temporary directory that's cleaned up after the test."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_panda3d():
    """Mock Panda3D modules for testing without requiring actual Panda3D installation."""
    mock_modules = {
        'panda3d': MagicMock(),
        'panda3d.core': MagicMock(),
        'direct': MagicMock(),
        'direct.showbase': MagicMock(),
        'direct.showbase.ShowBase': MagicMock(),
    }
    
    for module_name, mock_module in mock_modules.items():
        sys.modules[module_name] = mock_module
    
    yield mock_modules
    
    # Cleanup
    for module_name in mock_modules:
        if module_name in sys.modules:
            del sys.modules[module_name]


@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary for testing."""
    return {
        'pipeline': {
            'resolution': {'x': 1920, 'y': 1080},
            'enable_shadows': True,
            'shadow_quality': 'high',
            'enable_motion_blur': False,
            'msaa_samples': 4,
        },
        'plugins': {
            'bloom': {'enabled': True, 'intensity': 0.8},
            'ssao': {'enabled': True, 'radius': 0.5},
            'volumetrics': {'enabled': False},
        },
        'performance': {
            'gpu_memory_limit': 2048,
            'texture_compression': 'auto',
            'async_loading': True,
        }
    }


@pytest.fixture
def config_file(temp_dir, sample_config):
    """Create a temporary YAML config file."""
    config_path = temp_dir / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return config_path


@pytest.fixture
def mock_render_pipeline():
    """Mock RenderPipeline instance for testing."""
    mock_rp = Mock()
    mock_rp.settings = {
        'resolution': (1920, 1080),
        'shadows_enabled': True,
        'plugins': [],
    }
    mock_rp.showbase = Mock()
    mock_rp.light_manager = Mock()
    mock_rp.task_manager = Mock()
    return mock_rp


@pytest.fixture
def mock_light():
    """Mock light object for testing."""
    mock_light = Mock()
    mock_light.position = (0, 0, 10)
    mock_light.color = (1, 1, 1)
    mock_light.intensity = 1.0
    mock_light.shadow_enabled = True
    return mock_light


@pytest.fixture
def mock_plugin():
    """Mock plugin instance for testing."""
    mock_plugin = Mock()
    mock_plugin.name = "TestPlugin"
    mock_plugin.enabled = True
    mock_plugin.settings = {}
    mock_plugin.on_stage_setup = Mock()
    mock_plugin.on_pipeline_created = Mock()
    return mock_plugin


@pytest.fixture
def sample_shader_code():
    """Provide sample shader code for testing."""
    return {
        'vertex': """
#version 330
in vec3 position;
in vec2 texcoord;
out vec2 v_texcoord;
uniform mat4 mvp;

void main() {
    gl_Position = mvp * vec4(position, 1.0);
    v_texcoord = texcoord;
}
""",
        'fragment': """
#version 330
in vec2 v_texcoord;
out vec4 fragColor;
uniform sampler2D tex;

void main() {
    fragColor = texture(tex, v_texcoord);
}
"""
    }


@pytest.fixture
def mock_texture():
    """Mock texture object for testing."""
    mock_tex = Mock()
    mock_tex.width = 1024
    mock_tex.height = 1024
    mock_tex.format = "RGBA8"
    mock_tex.data = b'\x00' * (1024 * 1024 * 4)
    return mock_tex


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up the test environment for all tests."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set test environment variable
    monkeypatch.setenv("RENDERPIPELINE_TESTING", "1")
    
    # Mock any problematic imports during testing
    monkeypatch.setattr("sys.platform", "linux", raising=False)


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    logs = []
    
    def log_capture(level, message):
        logs.append({'level': level, 'message': message})
    
    return log_capture, logs


# Markers for different test categories
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "requires_panda3d: mark test as requiring Panda3D installation"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: mark test as requiring GPU access"
    )


# Skip tests that require Panda3D if it's not installed
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests based on requirements."""
    skip_panda3d = pytest.mark.skip(reason="Panda3D not installed")
    skip_gpu = pytest.mark.skip(reason="GPU not available")
    
    for item in items:
        if "requires_panda3d" in item.keywords:
            try:
                import panda3d.core
            except ImportError:
                item.add_marker(skip_panda3d)
        
        if "requires_gpu" in item.keywords:
            # Simple check for GPU availability
            if not os.environ.get("DISPLAY") and sys.platform != "win32":
                item.add_marker(skip_gpu)