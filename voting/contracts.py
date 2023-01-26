from pyteal import *


def approval_program():
    on_creation = Seq(
        [
            App.globalPut(Bytes("Creator"), Txn.sender()),
            Assert(Txn.application_args.length() == Int(5)),
            App.globalPut(Bytes("RegBegin"), Btoi(Txn.application_args[0])),
            App.globalPut(Bytes("RegEnd"), Btoi(Txn.application_args[1])),
            App.globalPut(Bytes("VoteBegin"), Btoi(Txn.application_args[2])),
            App.globalPut(Bytes("VoteEnd"), Btoi(Txn.application_args[3])),
            # adding voting token
            App.globalPut(Bytes("VotingToken"), Txn.application_args[4]),
            App.globalPut(Bytes("YesCount"), Int(0)),
            App.globalPut(Bytes("NoCount"), Int(0)),
            Return(Int(1)),
        ]
    )

    is_creator = Txn.sender() == App.globalGet(Bytes("Creator"))

    get_vote_of_sender = App.localGetEx(Int(0), App.id(), Bytes("voted"))
    get_asset_holding = AssetHolding.balance(Int(0), App.globalGet(Bytes("VotingToken")))

    on_closeout = Seq(
        [
            get_vote_of_sender,
            get_asset_holding,
            If(
                And(
                    Global.round() <= App.globalGet(Bytes("VoteEnd")),
                    get_vote_of_sender.hasValue(),
                    get_asset_holding.hasValue(),
                    get_vote_of_sender.value() == Bytes("Yes") or Bytes("No") or Bytes("Abstain"),
                ),
                If(get_vote_of_sender.value() == Bytes("Yes"))
                .Then(App.globalPut(Bytes("YesCount"), App.globalGet(Bytes("YesCount")) - get_asset_holding.value()))
                .ElseIf(get_vote_of_sender.value() == Bytes("No"))
                .Then(App.globalPut(Bytes("NoCount"), App.globalGet(Bytes("NoCount")) + get_asset_holding.value()))
                .ElseIf(get_vote_of_sender.value() == Bytes("Abstain"))
                .Then(Return(Int(1))),
            ),
            Return(Int(1)),
        ]
    )

    on_register = Return(
        And(
            Global.round() >= App.globalGet(Bytes("RegBegin")),
            Global.round() <= App.globalGet(Bytes("RegEnd")),
        )
    )

    on_vote = Seq(
        [
            get_vote_of_sender,
            get_asset_holding,
            Assert(
                And(
                    Global.round() >= App.globalGet(Bytes("VoteBegin")),
                    Global.round() <= App.globalGet(Bytes("VoteEnd")),
                    get_vote_of_sender.hasValue(),
                    get_asset_holding.hasValue(),
                    get_vote_of_sender.value() == Bytes("Yes") or Bytes("No") or Bytes("Abstain"),
                    # requirement for the vote sender to have at least 1000 voting tokens
                    get_asset_holding.value() >= Int(1000),
                )
            ),
            If(get_vote_of_sender.value() == Bytes("Yes"))
            .Then(App.globalPut(Bytes("YesCount"), App.globalGet(Bytes("YesCount")) + get_asset_holding.value()))
            .ElseIf(get_vote_of_sender.value() == Bytes("No"))
            .Then(App.globalPut(Bytes("NoCount"), App.globalGet(Bytes("NoCount")) - get_asset_holding.value()))
            .ElseIf(get_vote_of_sender.value() == Bytes("Abstain"))
            .Then(Return(Int(1))),
            App.localPut(Int(0), Bytes("voted"), Int(1)),
            Return(Int(1)),
        ]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, on_register],
        [Txn.application_args[0] == Bytes("vote"), on_vote],
    )

    return program


def clear_state_program():
    get_vote_of_sender = App.localGetEx(Int(0), App.id(), Bytes("voted"))
    program = Seq(
        [
            get_vote_of_sender,
            If(
                And(
                    Global.round() <= App.globalGet(Bytes("VoteEnd")),
                    get_vote_of_sender.hasValue(),
                ),
                App.globalPut(
                    get_vote_of_sender.value(),
                    App.globalGet(get_vote_of_sender.value()) - Int(1),
                ),
            ),
            Return(Int(1)),
        ]
    )

    return program


if __name__ == "__main__":
    with open("vote_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=2)
        f.write(compiled)

    with open("vote_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=2)
        f.write(compiled)