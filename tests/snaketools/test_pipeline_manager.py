import os
import subprocess

import pytest

from sequana_pipetools import snaketools, SequanaConfig, Module

from .. import test_dir


def test_pipeline_manager(tmpdir):
    # test missing input_directory
    cfg = SequanaConfig({})
    with pytest.raises(KeyError):
        pm = snaketools.PipelineManager("custom", cfg)

    # normal behaviour but no input provided:
    config = Module("fastqc")._get_config()
    cfg = SequanaConfig(config)
    cfg.cleanup()  # remove templates
    with pytest.raises(ValueError):
        pm = snaketools.PipelineManager("custom", cfg)

    # normal behaviour
    cfg = SequanaConfig(config)
    cfg.cleanup()  # remove templates
    file1 = os.path.join(test_dir, "data", "Hm2_GTGAAA_L005_R1_001.fastq.gz")
    cfg.config.input_directory, cfg.config.input_pattern = os.path.split(file1)
    pm = snaketools.PipelineManager("custom", cfg)
    assert not pm.paired

    cfg = SequanaConfig(config)
    cfg.cleanup()  # remove templates
    cfg.config.input_directory, cfg.config.input_pattern = os.path.split(file1)
    cfg.config.input_pattern = "Hm*gz"
    pm = snaketools.PipelineManager("custom", cfg)
    pm.plot_stats()
    assert pm.paired

    pm.getlogdir("fastqc")
    pm.getwkdir("fastqc")
    pm.getrawdata()
    pm.getreportdir("test")
    pm.getname("fastqc")

    # Test different configuration of input_directory, input_readtag,
    # input_pattern
    # Test the _R[12]_ paired
    working_dir = tmpdir.mkdir('test_Rtag_pe')
    cfg = SequanaConfig()
    cfgname = working_dir / "config.yaml"
    cfg.config.input_pattern = "*fastq.gz"
    cfg.config.input_directory = str(working_dir)
    cfg.config.input_readtag = "_R[12]_"
    cfg._update_yaml()
    cfg.save(cfgname)
    cmd = f"touch {working_dir}/test_R1_.fastq.gz"
    subprocess.call(cmd.split())
    cmd = f"touch {working_dir}/test_R2_.fastq.gz"
    subprocess.call(cmd.split())
    pm = snaketools.PipelineManager("test", str(cfgname))
    assert pm.paired

    # Test the _[12]. paired
    working_dir = tmpdir.mkdir('test_tag_pe')
    cfg = SequanaConfig()
    cfgname = working_dir / "config.yaml"
    cfg.config.input_pattern = "*fastq.gz"
    cfg.config.input_directory = str(working_dir)
    cfg.config.input_readtag = "_[12]."
    cfg._update_yaml()
    cfg.save(cfgname)
    cmd = f"touch {working_dir}/test_1.fastq.gz"
    subprocess.call(cmd.split())
    cmd = f"touch {working_dir}/test_2.fastq.gz"
    subprocess.call(cmd.split())
    pm = snaketools.PipelineManager("test", str(cfgname))
    assert pm.paired

    # Test the _R[12]_ single end
    working_dir = tmpdir.mkdir('test_Rtag_se')
    cfg = SequanaConfig()
    cfgname = working_dir / "config.yaml"
    cfg.config.input_pattern = "*fastq.gz"
    cfg.config.input_directory = str(working_dir)
    cfg.config.input_readtag = "_R[12]_"
    cfg._update_yaml()
    cfg.save(cfgname)
    cmd = f"touch {working_dir}/test_R1_.fastq.gz"
    subprocess.call(cmd.split())
    pm = snaketools.PipelineManager("test", str(cfgname))
    assert not pm.paired

    # Test the _R[12]_ single end
    working_dir = tmpdir.mkdir('test_tag_se')
    cfg = SequanaConfig()
    cfgname = working_dir / "config.yaml"
    cfg.config.input_pattern = "*fq.gz"  # wrong on purpose
    cfg.config.input_directory = str(working_dir)
    cfg.config.input_readtag = "_R[12]_"
    cfg._update_yaml()
    cfg.save(cfgname)
    cmd = f"touch {working_dir}/test_R1_.fastq.gz"
    subprocess.call(cmd.split())
    try:
        pm = snaketools.PipelineManager("test", str(cfgname))
    except ValueError:
        assert True


def test_pipeline_manager_generic(tmpdir):
    cfg = SequanaConfig({})
    file1 = os.path.join(test_dir, "data", "Hm2_GTGAAA_L005_R1_001.fastq.gz")
    cfg.config.input_directory, cfg.config.input_pattern = os.path.split(file1)
    cfg.config.input_pattern = "Hm*gz"
    pm = snaketools.pipeline_manager.PipelineManagerGeneric("fastqc", cfg)
    pm.getlogdir("fastqc")
    pm.getwkdir("fastqc")
    pm.getrawdata()
    pm.getreportdir("test")
    pm.getname("fastqc")
    gg = globals()
    gg["__snakefile__"] = "dummy"
    pm.setup(gg)
    del gg["__snakefile__"]

    class WF:
        included_stack = ["dummy", "dummy"]

    wf = WF()
    gg["workflow"] = wf
    pm.setup(gg)
    pm.teardown()

    multiqc = tmpdir.join('multiqc.html')
    with open(multiqc, 'w') as fh:
        fh.write("test")
    pm.clean_multiqc(multiqc)