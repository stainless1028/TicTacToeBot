from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption, ButtonStyle
from random import randint
from textwrap import dedent

o_emoji = nextcord.PartialEmoji.from_str("o:1226379343173910560")
x_emoji = nextcord.PartialEmoji.from_str("x:1226379383250354196")
blank_emoji = nextcord.PartialEmoji.from_str("background:1226409343591780403")


class TicTacToeButton(nextcord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=15)
        self.message = None
        self.player1 = player1
        self.player2 = player2
        self.players = [player1, player2]
        self.count = 0
        self.game_over = False

        if self.players[randint(0, 1)] == player1:
            self.p1 = {"player": player1, "emoji": o_emoji, "color": ButtonStyle.blurple, "pos": []}
            self.p2 = {"player": player2, "emoji": x_emoji, "color": ButtonStyle.red, "pos": []}
            self.turn = self.p1
        else:
            self.p1 = {"player": player1, "emoji": x_emoji, "color": ButtonStyle.red, "pos": []}
            self.p2 = {"player": player2, "emoji": o_emoji, "color": ButtonStyle.blurple, "pos": []}
            self.turn = self.p2

        self.row_value = 0
        for i in range(9):
            if i % 3 == 0:
                self.row_value += 1
            self.add_item(TTTButton(row=self.row_value, custom_id=str(i)))  # 버튼 추가(adding buttons)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content="15초간 응답이 없어 종료 되었습니다", view=self)
        self.stop()
        return

    async def win_check(self):
        winner = None
        pos1 = self.p1["pos"]
        pos2 = self.p2["pos"]
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
            if all(pos in pos1 for pos in winning_pos):
                winner = self.p1["player"]
                break
            elif all(pos in pos2 for pos in winning_pos):
                winner = self.p2["player"]
                break
        if winner is not None:
            for child in self.children:
                child.disabled = True
            message = dedent(f"""
            **{self.player1.name}** **vs.** **{self.player2.name}**
            {winner.mention}님이 이겼습니다!
            """)
            await self.message.edit(content=message, view=self)
            self.game_over = True
            self.stop()
            return

        if self.count == 9:
            message = dedent(f"""
            **{self.player1.name}** **vs.** **{self.player2.name}**

            무승부입니다
            """)
            await self.message.edit(content=message, view=self)
            self.game_over = True
            self.stop()
            return


class TTTButton(nextcord.ui.Button):
    def __init__(self, row: int, custom_id: str):
        super().__init__(label=None, style=ButtonStyle.gray, emoji=blank_emoji, row=row, custom_id=custom_id)

    async def switch_turn(self):
        parent_view: TicTacToeButton = self.view
        if parent_view.turn["player"] == parent_view.player1:
            parent_view.turn = parent_view.p2
        else:
            parent_view.turn = parent_view.p1
        return dedent(f"""
        **{parent_view.player1.name}** **vs.** **{parent_view.player2.name}**

        <@{parent_view.turn["player"].id}>님 차례입니다
        15초 안에 버튼을 눌러주세요!
        """)

    async def callback(self, interaction: Interaction):
        parent_view: TicTacToeButton = self.view
        if interaction.user == parent_view.turn["player"]:
            parent_view.count += 1
            self.disabled = True
            self.emoji = parent_view.turn["emoji"]
            self.style = parent_view.turn["color"]
            parent_view.turn["pos"].append(int(interaction.data["custom_id"]))
            parent_view.turn["pos"].sort()
            await parent_view.win_check()
            if not parent_view.game_over:
                message = await self.switch_turn()
                await interaction.response.edit_message(content=message, view=parent_view)
        elif interaction.user in parent_view.players and interaction.user != parent_view.turn["player"]:
            await interaction.response.send_message("상대의 차례입니다", ephemeral=True)
        else:
            await interaction.response.send_message("참가자가 아닙니다", ephemeral=True)


class Tictactoe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection NonAsciiCharacters,PyPep8Naming
    @nextcord.slash_command(name="틱택토", description="원하는 사람과 틱택토를 해보세요")
    async def 틱택토(self, interaction: Interaction, 상대: nextcord.Member = SlashOption(description="상대를 선택해 주세요", required=True)):
        player1 = interaction.user
        player2 = 상대

        if player1.id == player2.id:
            await interaction.send("혼자서는 플레이 할 수 없어요", ephemeral=True)
            return
        if player1.bot or player2.bot:
            await interaction.send("봇과는 플레이 할 수 없어요", ephemeral=True)
            return

        view = TicTacToeButton(player1, player2)

        message = dedent(f"""
        **{player1.name}** **vs.** **{player2.name}**

        <@{view.turn["player"].id}>님 차례입니다
        15초 안에 버튼을 눌러주세요!
        """)

        view.message = await interaction.send(message, view=view)
        await view.wait()


def setup(bot):
    bot.add_cog(Tictactoe(bot))
