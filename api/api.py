# encoding: utf-8
import json
import joblib
from urllib import response
from util.util import Util
from fastapi import HTTPException


class API:

    ######################################################################
    #ここにはVメイン処理になるようなもの、共通化できないものを記載してください。#
    ######################################################################
    def getDevArchType():
        """
        @param  void
        @return 開発環境の面数
        """
        return ['01', '02', '03', '04', '05', '06', '07']

    def getVmName(arch_num: int):
        """
        @param  arch_num 面の数
        @return server VM名称のARRAY
        """
        server = [
            "msdfr9-" + str(arch_num) + "-01v",
            "msdfr9-" + str(arch_num) + "-02v",
            "msdfr9-" + str(arch_num) + "-31v",
            "msdfr9-" + str(arch_num) + "-32v",
            "msdfr9-" + str(arch_num) + "-41v",
            "msdfr9-" + str(arch_num) + "-42v",
            "msdfr9-" + str(arch_num) + "-51v",
            "msdfr9-" + str(arch_num) + "-52v",
            "msdfr9-" + str(arch_num) + "-61v",
            "msdfr9-" + str(arch_num) + "-62v",
            "msdfr9-" + str(arch_num) + "-71v",
            "msdfr9-" + str(arch_num) + "-72v",
            "msdap9-" + str(arch_num) + "-01v",
            "msdap9-" + str(arch_num) + "-02v",
            "msdbt9-" + str(arch_num) + "-01v",
            "msdmn9-" + str(arch_num) + "-01v",
            "msddb9-" + str(arch_num) + "-01v",
            "msddb9-" + str(arch_num) + "-02v",
            "msdot9-" + str(arch_num) + "-01v"
        ]
        return server

    def isWorkVM(vmhost: str):
        """
        @param  vmhost VM名称
        @return Boolean ICPMコマンドの結果を返却します。
        """
        # PINGにて疎通チェック
        response = Util.command(["ping", "-n", "2", vmhost])

        if(response.returncode == 0):
            return True
        elif(response.returncode == 1):
            return False
        else:
            raise HTTPException(status_code=406, detail='PING_FUNCTION_ERROR')

    def getVmStatus(archType):
        """
        GETVMSTATUSメイン処理
        @param  void
        @return 現在の状態を返却
        """
        return_json_text = []

        vmList = API.getVmName(archType)
        # スレッド処理
        result = joblib.Parallel(
            n_jobs=-1, backend='threading')(joblib.delayed(API.isWorkVM)(vm) for vm in vmList)
        # ホスト合計
        TOTAL = len(result)
        # 起動中ホスト
        UP = 0
        # 停止中ホスト
        DOWN = 0
        # PING統計まとめ処理
        for status in result:
            if(status == True):
                UP += 1
            elif(status == False):
                DOWN += 1
        # ロックファイル削除処理
        lockReadFile = Util.lockRead(archType)
        if(lockReadFile == "START" and TOTAL == UP):
            Util.unlock(archType)
        elif(lockReadFile == "STOP" and TOTAL == DOWN):
            Util.unlock(archType)

        pending = False
        # ロックファイルが存在している且つ、UPとDOWNがTOTALの値ではない事
        if(lockReadFile != 'FILE_IS_NOT_EXISTS' or TOTAL != UP and TOTAL != DOWN):
            pending = True

        status = False
        # 停止中OR起動中のパラメータを設定する
        if(TOTAL == UP):
            status = True
        elif(TOTAL == DOWN):
            status = False
        else:
            status = False

        # 配列に格納
        return_json_text.append(
            {'ArchType': archType, 'TOTAL': TOTAL, 'UP': UP, 'DOWN': DOWN, 'Pending': pending, 'Status': status})
        return json.dumps(return_json_text)

    def getVmStatusMulti():
        """
        当関数はマルチスレッドで実行できるように、joblibを使用して、面ごとにpingを崇徳しております。
        @param  void
        @return 現在の状態を返却
        """
        # マルチスレッド処理
        return joblib.Parallel(n_jobs=-1, backend='threading')(joblib.delayed(API.getVmStatus)(archType) for archType in API.getDevArchType())


    def setVmStatus(VmChgParam):
        """
        @param  vmChgParam
        @return 各面のステータス情報とロック状況を返却
        """
        #排他ロックの面一覧
        vmStatusList = API.getVmStatusMulti()
        pendigArch=[]
        for getVmStatus in vmStatusList:
            status = json.loads(str(getVmStatus))[0]
            if(status['Pending']==True):
                pendigArch.append(status['ArchType'])

        for chgVmStatus in VmChgParam:
            #排他ロックがかかっている物があれば例外を返す
            if((chgVmStatus["ArchType"] in pendigArch) == True):
                raise HTTPException(status_code=406, detail='既に処理が進行中です。')
            #現在のステータスと変更仕様としているステータスに差異があればisExecをTrueに
            isExec=False
            for getVmStatus in vmStatusList:
                status = json.loads(str(getVmStatus))[0]
                if(status['Status']!=chgVmStatus["Status"]):
                    isExec=True
                else:
                    isExec=False
            if(isExec == True):
                #排他ロックをかける
                chgStatus=""
                if chgVmStatus["Status"] == True:
                    chgStatus = "START"
                elif chgVmStatus["Status"] == False:
                    chgStatus = "STOP"
                Util.lock(arch_num=chgVmStatus["ArchType"],set_process=chgStatus)

                #SystemWalkerコマンド実行
                #実行コマンド文生成
                command=[]
                if(chgVmStatus["Status"] == True):
                    command=['jobschcontrol','cm_ansible/'+'【D'+chgVmStatus["ArchType"].lstrip('0') +'】自動起動','start']
                else:
                    command=['jobschcontrol','cm_ansible/'+'【D'+chgVmStatus["ArchType"].lstrip('0') +'】自動停止',' start']
                print(command)

                #ジョブ実行
                ExecResult = Util.command(command)
                if(ExecResult.returncode == 1):
                    ##エラーが発生した場合排他ロックを解除
                    Util.unlock(arch_num=chgVmStatus["ArchType"])
                    raise HTTPException(status_code=406, detail=ExecResult.stderr)
            else:
                raise HTTPException(status_code=406, detail='要求ステータスと現状ステータスが同一のため、変更処理を実行できませんでした。')
                # Util.command('')
        return {'message':'StatusOK'}
