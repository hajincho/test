// Furina: developer weapon-select menu (Tab). Plain Slate buttons/text.
#include "Furina/FurinaWeaponMenuComponent.h"

#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SGridPanel.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Text/STextBlock.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(FurinaWeaponMenuComponent)

namespace FurinaWeaponMenu
{
	// 행 = 병과, 열 = 국가. 장교와 기갑병은 같은 권총.
	static const TCHAR* Classes[] = { TEXT("장교"), TEXT("보병"), TEXT("돌격병"), TEXT("대전차병"), TEXT("중화기병"), TEXT("저격수"), TEXT("기갑병") };
	static const TCHAR* Nations[] = { TEXT("독일"), TEXT("일본"), TEXT("이탈리아"), TEXT("미국"), TEXT("소련"), TEXT("영국") };
	static const TCHAR* Weapons[7][6] = {
		{ TEXT("P38"), TEXT("남부 14식"), TEXT("Beretta M34"), TEXT("M1911A1"), TEXT("TT-33"), TEXT("Enfield No.2") },
		{ TEXT("Kar98k"), TEXT("38식"), TEXT("Carcano M91"), TEXT("M1 Garand"), TEXT("Mosin M91/30"), TEXT("Lee-Enfield No.4") },
		{ TEXT("MP40"), TEXT("38식 소총"), TEXT("M38A"), TEXT("Thompson"), TEXT("PPSh-41"), TEXT("Sten Mk II") },
		{ TEXT("Panzerfaust"), TEXT("94식 37mm포"), TEXT("47/32"), TEXT("Bazooka"), TEXT("PTRD-41"), TEXT("PIAT") },
		{ TEXT("MG42"), TEXT("96식"), TEXT("Breda M30"), TEXT("BAR"), TEXT("DP-27"), TEXT("Bren") },
		{ TEXT("Kar98k ZF39"), TEXT("97식 저격총"), TEXT("Carcano M91*"), TEXT("M1903A4"), TEXT("Mosin PU"), TEXT("No.4 Mk I(T)") },
		{ TEXT("P38"), TEXT("남부 14식"), TEXT("Beretta M34"), TEXT("M1911A1"), TEXT("TT-33"), TEXT("Enfield No.2") },
	};
	static constexpr int32 NumClasses = UE_ARRAY_COUNT(Classes);
	static constexpr int32 NumNations = UE_ARRAY_COUNT(Nations);
}

class SFurinaWeaponMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SFurinaWeaponMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<UFurinaWeaponMenuComponent>, Owner)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		using namespace FurinaWeaponMenu;
		Owner = InArgs._Owner;
		const FSlateFontInfo TitleFont = FCoreStyle::GetDefaultFontStyle("Bold", 18);
		const FSlateFontInfo HeadFont = FCoreStyle::GetDefaultFontStyle("Bold", 12);
		const FSlateFontInfo CellFont = FCoreStyle::GetDefaultFontStyle("Regular", 11);

		TSharedRef<SGridPanel> Grid = SNew(SGridPanel);
		Grid->AddSlot(0, 0).Padding(4)[SNew(STextBlock).Font(HeadFont).Text(FText::FromString(TEXT("병과 \\ 국가")))];
		for (int32 N = 0; N < NumNations; ++N)
		{
			Grid->AddSlot(N + 1, 0).Padding(4).HAlign(HAlign_Center)[SNew(STextBlock).Font(HeadFont).Text(FText::FromString(Nations[N]))];
		}
		for (int32 C = 0; C < NumClasses; ++C)
		{
			Grid->AddSlot(0, C + 1).Padding(4).VAlign(VAlign_Center)[SNew(STextBlock).Font(HeadFont).Text(FText::FromString(Classes[C]))];
			for (int32 N = 0; N < NumNations; ++N)
			{
				const FString W = Weapons[C][N];
				Grid->AddSlot(N + 1, C + 1).Padding(2)
				[
					SNew(SBox).WidthOverride(130.f)
					[
						SNew(SButton)
						.HAlign(HAlign_Center)
						.IsEnabled_Lambda([this, W]() { return Owner.IsValid() && Owner->EnabledWeapons.Contains(W); })
						.ToolTipText_Lambda([this, W]() { return FText::FromString((Owner.IsValid() && Owner->EnabledWeapons.Contains(W)) ? W : W + TEXT(" (아직 추가 안 됨)")); })
						.OnClicked_Lambda([this, C, N]() { if (Owner.IsValid()) { Owner->HandleWeaponPressed(C, N); } return FReply::Handled(); })
						[
							SNew(STextBlock).Font(CellFont).Text(FText::FromString(W))
						]
					]
				];
			}
		}

		ChildSlot
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.02f, 0.02f, 0.03f, 0.88f))
			.Padding(16.f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 8)
				[SNew(STextBlock).Font(TitleFont).Text(FText::FromString(TEXT("무기 선택 (개발자용)    Tab / Esc: 닫기")))]
				+ SVerticalBox::Slot().AutoHeight().Padding(0, 4)
				[SNew(STextBlock).Font(HeadFont).Text(FText::FromString(TEXT("1번 무기 (주무기)  -  회색 버튼은 아직 추가되지 않은 무기")))]
				+ SVerticalBox::Slot().AutoHeight()[Grid]
				+ SVerticalBox::Slot().AutoHeight().Padding(0, 12, 0, 4)
				[SNew(STextBlock).Font(HeadFont).Text(FText::FromString(TEXT("2번 무기 (근접: 삽 / 칼 등)  -  비어 있음")))]
				+ SVerticalBox::Slot().AutoHeight().Padding(0, 8, 0, 0)
				[
					SNew(STextBlock).Font(CellFont)
					.Text_Lambda([this]()
					{
						const FString P = Owner.IsValid() && !Owner->SelectedPrimary.IsEmpty() ? Owner->SelectedPrimary : FString(TEXT("없음"));
						const FString M = Owner.IsValid() && !Owner->SelectedMelee.IsEmpty() ? Owner->SelectedMelee : FString(TEXT("없음"));
						return FText::FromString(FString::Printf(TEXT("현재 선택  1번: %s   /   2번: %s"), *P, *M));
					})
				]
				+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right).Padding(0, 8, 0, 0)
				[
					SNew(SButton)
					.OnClicked_Lambda([this]() { if (Owner.IsValid()) { Owner->CloseMenu(); } return FReply::Handled(); })
					[SNew(STextBlock).Font(HeadFont).Text(FText::FromString(TEXT("닫기")))]
				]
			]
		];
	}

	virtual bool SupportsKeyboardFocus() const override { return true; }

	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override
	{
		if (InKeyEvent.GetKey() == EKeys::Tab || InKeyEvent.GetKey() == EKeys::Escape)
		{
			if (Owner.IsValid())
			{
				Owner->CloseMenu();
			}
			return FReply::Handled();
		}
		return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
	}

private:
	TWeakObjectPtr<UFurinaWeaponMenuComponent> Owner;
};

TArray<FString> UFurinaWeaponMenuComponent::GetClassNames()
{
	TArray<FString> Out;
	for (const TCHAR* S : FurinaWeaponMenu::Classes) { Out.Add(S); }
	return Out;
}

TArray<FString> UFurinaWeaponMenuComponent::GetNationNames()
{
	TArray<FString> Out;
	for (const TCHAR* S : FurinaWeaponMenu::Nations) { Out.Add(S); }
	return Out;
}

FString UFurinaWeaponMenuComponent::GetWeaponName(int32 ClassIndex, int32 NationIndex)
{
	if (ClassIndex < 0 || ClassIndex >= FurinaWeaponMenu::NumClasses || NationIndex < 0 || NationIndex >= FurinaWeaponMenu::NumNations)
	{
		return FString();
	}
	return FurinaWeaponMenu::Weapons[ClassIndex][NationIndex];
}

APlayerController* UFurinaWeaponMenuComponent::GetOwningPC() const
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	return Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
}

void UFurinaWeaponMenuComponent::ToggleMenu()
{
	if (IsMenuOpen())
	{
		CloseMenu();
	}
	else
	{
		OpenMenu();
	}
}

void UFurinaWeaponMenuComponent::OpenMenu()
{
	if (IsMenuOpen())
	{
		return;
	}
	APlayerController* PC = GetOwningPC();
	ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
	if (!LP || !LP->ViewportClient)
	{
		return;
	}
	TSharedRef<SFurinaWeaponMenu> Menu = SNew(SFurinaWeaponMenu).Owner(this);
	MenuWidget = SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Center).Visibility(EVisibility::SelfHitTestInvisible)[Menu];
	LP->ViewportClient->AddViewportWidgetContent(MenuWidget.ToSharedRef(), 1000);

	bPrevShowCursor = PC->ShouldShowMouseCursor();
	PC->SetShowMouseCursor(true);
	FInputModeUIOnly Mode;
	Mode.SetWidgetToFocus(Menu);
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	PC->SetInputMode(Mode);
	FSlateApplication::Get().SetKeyboardFocus(Menu, EFocusCause::SetDirectly);
}

void UFurinaWeaponMenuComponent::CloseMenu()
{
	if (!MenuWidget.IsValid())
	{
		return;
	}
	APlayerController* PC = GetOwningPC();
	ULocalPlayer* LP = PC ? PC->GetLocalPlayer() : nullptr;
	if (LP && LP->ViewportClient)
	{
		LP->ViewportClient->RemoveViewportWidgetContent(MenuWidget.ToSharedRef());
	}
	MenuWidget.Reset();
	if (PC)
	{
		PC->SetShowMouseCursor(bPrevShowCursor);
		PC->SetInputMode(FInputModeGameOnly());
	}
}

void UFurinaWeaponMenuComponent::HandleWeaponPressed(int32 ClassIndex, int32 NationIndex)
{
	const FString W = GetWeaponName(ClassIndex, NationIndex);
	if (W.IsEmpty() || !EnabledWeapons.Contains(W))
	{
		return;
	}
	SelectedPrimary = W;
	OnWeaponChosen.Broadcast(1, FurinaWeaponMenu::Classes[ClassIndex], FurinaWeaponMenu::Nations[NationIndex], W);
	CloseMenu();
}

void UFurinaWeaponMenuComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	CloseMenu();
	Super::EndPlay(EndPlayReason);
}
