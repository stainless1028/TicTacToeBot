from nextcord.ext import commands
import nextcord
from nextcord import Interaction, SlashOption, ButtonStyle
from random import randint

active_servers: dict[int, "TicTacToeGame"] = {}

O_EMOJI = nextcord.PartialEmoji.from_str("o:1226379343173910560")
X_EMOJI = nextcord.PartialEmoji.from_str("x:1226379383250354196")
BLANK_EMOJI = nextcord.PartialEmoji.from_str("background:1226409343591780403")
WINNING_CONDITIONS = [
    {0, 1, 2}, {3, 4, 5}, {6, 7, 8},  # 가로
    {0, 3, 6}, {1, 4, 7}, {2, 5, 8},  # 세로
    {0, 4, 8}, {2, 4, 6},             # 대각선
]

class TicTacToeGame:
    """단일 게임 관리 클래스"""

    def __init__(self, interaction: Interaction, player1: nextcord.Member, player2: nextcord.Member):
        self.interaction = interaction
        self.message = None
        self.game_over = False
        self.move_count = 0

        turn_init = randint(0, 1)
        if turn_init == 0:
            self.p1_info = {"player": player1, "emoji": O_EMOJI, "color": ButtonStyle.blurple, "pos": set()}
            self.p2_info = {"player": player2, "emoji": X_EMOJI, "color": ButtonStyle.red, "pos": set()}
        else:
            self.p1_info = {"player": player1, "emoji": X_EMOJI, "color": ButtonStyle.red, "pos": set()}
            self.p2_info = {"player": player2, "emoji": O_EMOJI, "color": ButtonStyle.blurple, "pos": set()}

        self.turn = self.p1_info if turn_init == 0 else self.p2_info
        self.view = TicTacToeView(self)

    def switch_turn(self):
        self.turn = self.p2_info if self.turn == self.p1_info else self.p1_info

    def get_message(self, message: str) -> str:
        header = f"**{self.p1_info["player"].name}** **vs.** **{self.p2_info["player"].name}**"
        return f"{header}\n\n{message}"

    async def start(self):
        active_servers[self.interaction.guild_id] = self

        initial_message = self.get_message(f"<@{self.turn["player"].id}>님 차례입니다\n15초 안에 버튼을 눌러주세요!")
        self.message = await self.interaction.send(initial_message, view=self.view)

        await self.view.wait()
        self.cleanup()

    async def check_win(self):
        winner = None
        p1_pos = self.p1_info["pos"]
        p2_pos = self.p2_info["pos"]

        for condition in WINNING_CONDITIONS:
            if condition.issubset(p1_pos):
                winner = self.p1_info["player"]
                break
            if condition.issubset(p2_pos):
                winner = self.p2_info["player"]
                break

        if winner is not None:
            await self.end_game(f"{winner.mention}님이 이겼습니다!")
        elif self.move_count == 9:
            await self.end_game("무승부 입니다")

    async def end_game(self, message: str):
        """게임 종료(버튼 비활성화와 메시지 수정)"""
        if self.game_over:
            return
        self.game_over = True

        final_message = self.get_message(message)
        for button in self.view.children:
            button.disabled = True

        try:
            await self.message.edit(content=final_message, view=self.view)
        except nextcord.NotFound:  # 메시지가 삭제된 경우
            pass
        self.view.stop()

    def cleanup(self):
        if self.interaction.guild_id in active_servers:
            del active_servers[self.interaction.guild_id]


class TicTacToeView(nextcord.ui.View):
    """버튼 전체 관리"""

    def __init__(self, game: TicTacToeGame):
        super().__init__(timeout=15)
        self.game = game
        prefix = self.game.interaction.id

        # 3x3 버튼 추가
        for i in range(9):
            btn_id = f"{prefix}:{i}"
            self.add_item(TTTButton(row=(i // 3), custom_id=btn_id))

    async def on_timeout(self):
        if not self.game.game_over:
            await self.game.end_game("15초간 응답이 없어 종료 되었습니다")


class TTTButton(nextcord.ui.Button):
    """개별 버튼"""

    def __init__(self, row: int, custom_id: str):
        # blank emoji를 넣어주지 않으면 모바일에서 버튼 크기가 이상해 보임
        super().__init__(label=None, style=ButtonStyle.gray, emoji=BLANK_EMOJI, row=row, custom_id=custom_id)

    async def callback(self, interaction: Interaction):
        # 버튼 클릭 시 호출
        game: TicTacToeGame = self.view.game

        if interaction.user not in {game.p1_info["player"], game.p2_info["player"]}:
            await interaction.response.send_message("참가자가 아닙니다", ephemeral=True)
            return

        if interaction.user != game.turn["player"]:
            await interaction.response.send_message("상대의 차례입니다", ephemeral=True)
            return

        current_player = game.turn
        self.disabled = True
        self.emoji = current_player["emoji"]
        self.style = current_player["color"]
        game.move_count += 1
        current_player["pos"].add(int(self.custom_id[-1]))

        await game.check_win()

        if not game.game_over:
            game.switch_turn()
            message = game.get_message(f"<@{game.turn["player"].id}>님 차례입니다\n15초 안에 버튼을 눌러주세요!")
            await interaction.response.edit_message(content=message, view=self.view)


class Tictactoe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(name="틱택토", description="원하는 사람과 틱택토를 해보세요")
    async def tictactoe_command(
            self,
            interaction: Interaction,
            opponent: nextcord.Member = SlashOption(
                name="상대",
                description="상대를 선택해 주세요",
                required=True
            )
    ):
        if interaction.guild_id in active_servers:
            await interaction.send("서버에 이미 진행중인 게임이 있어요.", delete_after=5)
            return

        if interaction.user.id == opponent.id:
            await interaction.send("혼자서는 플레이 할 수 없어요", ephemeral=True)
            return
        if opponent.bot:
            await interaction.send("봇과는 플레이 할 수 없어요", ephemeral=True)
            return

        game = TicTacToeGame(interaction, interaction.user, opponent)
        await game.start()


def setup(bot):
    bot.add_cog(Tictactoe(bot))
