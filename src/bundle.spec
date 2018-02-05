block_cipher = None
task_a = Analysis(['task.py'],
             pathex=['/home/klaus/dev/mpdqmc/src'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

job_a = Analysis(['job.py'],
             pathex=['/home/klaus/dev/mpdqmc/src'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

mpdqmc_a = Analysis(['mpdqmc.py'],
             pathex=['/home/klaus/dev/mpdqmc/src'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

MERGE( (task_a, 'task', 'task'), (job_a, 'job', 'job'), (mpdqmc_a, 'mpdqmc', 'mpdqmc') )

task_pyz = PYZ(task_a.pure, task_a.zipped_data,
             cipher=block_cipher)
task_exe = EXE(task_pyz,
          task_a.scripts,
          task_a.binaries,
          task_a.zipfiles,
          task_a.datas,
          name='task',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )

job_pyz = PYZ(job_a.pure, job_a.zipped_data,
             cipher=block_cipher)

job_exe = EXE(job_pyz,
          job_a.scripts,
          job_a.binaries,
          job_a.zipfiles,
          job_a.datas,
          name='job',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )


mpdqmc_pyz = PYZ(mpdqmc_a.pure, mpdqmc_a.zipped_data,
             cipher=block_cipher)

mpdqmc_exe = EXE(mpdqmc_pyz,
          mpdqmc_a.scripts,
          mpdqmc_a.binaries,
          mpdqmc_a.zipfiles,
          mpdqmc_a.datas,
          name='mpdqmc',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
