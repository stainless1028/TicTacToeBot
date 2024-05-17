from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption, ButtonStyle
from random import randint
from textwrap import dedent

o_emoji = nextcord.PartialEmoji.from_str("o:1226379343173910560")
x_emoji = nextcord.PartialEmoji.from_str("x:1226379383250354196")
bg_emoji = nextcord.PartialEmoji.from_str("background:1226409343591780403")


class TicTacToeButton(nextcord.ui.View):
    row_value = 0

    def __init__(self):
        super().__init__(timeout=15)
        self.message = None
        for i in range(9):
            if i % 3 == 0:
                self.row_value += 1
            self.add_item(TTTButton(row=self.row_value, custom_id=str(i)))  # 버튼 추가

    async def on_timeout(self):
        print(self.message)
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="15초간 응답이 없어 종료 되었습니다", view=self)
        self.stop()
        return

    async def win_check(self):
        # noinspection PyGlobalUndefined
        global game_over
        winner = None
        pos1 = p1["pos"]
        pos2 = p2["pos"]
        winning_conditions = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            [0, 4, 8],
            [2, 4, 6],
        ]
        for winning_pos in winning_conditions:
            if winning_pos[0] in pos1 and winning_pos[1] in pos1 and winning_pos[2] in pos1:
                winner = p1["player"]
            elif winning_pos[0] in pos2 and winning_pos[1] in pos2 and winning_pos[2] in pos2:
                winner = p2["player"]
            if winner is not None:
                for child in self.children:
                    child.disabled = True
                message = dedent(f"""
            **{player1.name}** **vs.** **{player2.name}**

            {winner.mention}님이 이겼습니다!
            """)
                await self.message.edit(content=message, view=self)
                game_over = True
                self.stop()
                return

        if count == 9:
            message = dedent(f"""
            **{player1.name}** **vs.** **{player2.name}**

            무승부입니다
            """)
            await self.message.edit(content=message, view=self)
            game_over = True
            self.stop()
            return


class TTTButton(nextcord.ui.Button):
    def __init__(self, row: int, custom_id: str):
        super().__init__(label=None, style=ButtonStyle.gray, emoji=bg_emoji, row=row, custom_id=custom_id)

    async def switch_turn(self):
        # noinspection PyGlobalUndefined
        global turn

        if turn["player"] == player1:
            turn = p2
            return dedent(f"""
            **{player1.name}** **vs.** **{player2.name}**

            <@{turn["player"].id}>님 차례입니다
            15초 안에 버튼을 눌러주세요!
            """)
        else:
            turn = p1
            return dedent(f"""
            **{player1.name}** **vs.** **{player2.name}**

            <@{turn["player"].id}>님 차례입니다
            15초 안에 버튼을 눌러주세요!
            """)

    async def callback(self, interaction):  # 버튼 클릭시
        # noinspection PyGlobalUndefined
        global count
        if interaction.user == turn["player"]:
            count += 1
            self.disabled = True
            self.emoji = turn["emoji"]
            self.style = turn["color"]
            turn["pos"].append(int(interaction.data["custom_id"]))
            turn["pos"].sort()
            await view.win_check()
            if not game_over:
                message = await self.switch_turn()
                await interaction.response.edit_message(content=message, view=self.view)
                return
        elif interaction.user in players and interaction.user != turn:
            await interaction.response.send_message("상대의 차례입니다", ephemeral=True)
            return
        else:
            await interaction.response.send_message("참가자가 아닙니다", ephemeral=True)
            return


# noinspection PyGlobalUndefined
class Tictactoe(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # noinspection PyPep8Naming,NonAsciiCharacters
    @nextcord.slash_command(name="틱택토", description="원하는 사람과 틱택토를 해보세요")
    async def 틱택토(self, interaction: Interaction,
                  상대: nextcord.Member = SlashOption(description="상대를 선택해 주세요", required=True)):
        global player1, player2, turn, p1, p2, players, count, view, game_over

        view = TicTacToeButton()
        game_over = False

        player1 = interaction.user
        player2 = 상대
        players = [player1, player2]
        count = 0

        if player1.id == player2.id:  # 동일인물 금지
            await interaction.send("혼자서는 플레이 할 수 없어요", ephemeral=True)
            return
        if player1.bot is True or player2.bot is True:  # 봇 금지
            await interaction.send("봇과는 플레이 할 수 없어요", ephemeral=True)
            return

        if players[randint(0, 1)] == player1:  # 랜덤으로 순서 결정
            p1 = {"player": player1, "emoji": o_emoji, "color": ButtonStyle.blurple, "pos": []}
            p2 = {"player": player2, "emoji": x_emoji, "color": ButtonStyle.red, "pos": []}
            turn = p1
        else:
            p1 = {"player": player1, "emoji": x_emoji, "color": ButtonStyle.red, "pos": []}
            p2 = {"player": player2, "emoji": o_emoji, "color": ButtonStyle.blurple, "pos": []}
            turn = p2

        message = dedent(f"""
        **{player1.name}** **vs.** **{player2.name}**

        <@{turn["player"].id}>님 차례입니다
        15초 안에 버튼을 눌러주세요!
        """)

        view.message = await interaction.send(message, view=view)
        await view.wait()


def setup(bot):
    bot.add_cog(Tictactoe(bot))
