# encoding: utf-8
import subprocess
from fastapi import HTTPException
import os
class Util:
    def command(command):
        """
        @param  command 実行コマンドの引数
        @return res.stdout 実行コマンドの標準出力
        @return res.stderr 実行コマンドの標準エラー出力
        """
        try:
            res = subprocess.run(
                command, stdout=subprocess.PIPE, shell=True, encoding="shift-jis")
        except:
            print('エラー発生')
        return res

    def lock(arch_num:str,set_process:str):
        """
        @param  arch_num 面数
        @return set_process これから変更しようとしているステータス
        @return NONE
        """
        if(set_process != 'STOP' and set_process !='START'):
            raise  HTTPException(status_code=401, detail='SET_PROCESS_VALUE_ERROR')
        f = open('./util/LOCKFILE/lock'+arch_num, 'w', encoding='UTF-8')
        f.write(set_process)
        f.close()

    def lockRead(arch_num:str):
        """
        @param  arch_num 面数
        @return data これから変更しようとしているステータスの値を格納
        """
        if os.path.exists('./util/LOCKFILE/lock'+arch_num) == True:
            f = open('./util/LOCKFILE/lock'+arch_num, 'r')
            data = f.read()
            f.close()
            return data
        else:
            return 'FILE_IS_NOT_EXISTS'

    def unlock(arch_num:str):
        """
        @param  arch_num 面数
        @return NONE
        """
        if os.path.exists('./util/LOCKFILE/lock'+arch_num) == True:
            os.remove('./util/LOCKFILE/lock'+arch_num)
        else:
            return 'FILE_IS_NOT_EXISTS'