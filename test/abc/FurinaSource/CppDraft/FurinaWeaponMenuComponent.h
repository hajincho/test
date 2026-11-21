// Furina: developer weapon-select menu (Tab). Plain Slate buttons/text, no UMG asset.
#pragma once

#include "Components/ActorComponent.h"
#include "FurinaWeaponMenuComponent.generated.h"

class SWidget;

/** Slot 1 = primary weapons (class x nation table), Slot 2 = melee (empty for now). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(FFurinaWeaponChosen, int32, Slot, const FString&, ClassName, const FString&, Nation, const FString&, Weapon);

UCLASS(ClassGroup = (Furina), meta = (BlueprintSpawnableComponent))
class LYRAGAME_API UFurinaWeaponMenuComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	/** Weapon names that are implemented. Only these buttons can be pressed; all others are greyed out. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Furina|WeaponMenu")
	TArray<FString> EnabledWeapons;

	/** Last chosen primary (slot 1) and melee (slot 2) weapon names. Empty = none. */
	UPROPERTY(BlueprintReadOnly, Category = "Furina|WeaponMenu")
	FString SelectedPrimary;

	UPROPERTY(BlueprintReadOnly, Category = "Furina|WeaponMenu")
	FString SelectedMelee;

	/** Fired when an enabled weapon button is pressed. Hook the actual weapon swap here later. */
	UPROPERTY(BlueprintAssignable, Category = "Furina|WeaponMenu")
	FFurinaWeaponChosen OnWeaponChosen;

	UFUNCTION(BlueprintCallable, Category = "Furina|WeaponMenu")
	void ToggleMenu();

	UFUNCTION(BlueprintCallable, Category = "Furina|WeaponMenu")
	void OpenMenu();

	UFUNCTION(BlueprintCallable, Category = "Furina|WeaponMenu")
	void CloseMenu();

	UFUNCTION(BlueprintPure, Category = "Furina|WeaponMenu")
	bool IsMenuOpen() const { return MenuWidget.IsValid(); }

	/** Table data (rows = classes, columns = nations). */
	UFUNCTION(BlueprintPure, Category = "Furina|WeaponMenu")
	static TArray<FString> GetClassNames();

	UFUNCTION(BlueprintPure, Category = "Furina|WeaponMenu")
	static TArray<FString> GetNationNames();

	UFUNCTION(BlueprintPure, Category = "Furina|WeaponMenu")
	static FString GetWeaponName(int32 ClassIndex, int32 NationIndex);

	void HandleWeaponPressed(int32 ClassIndex, int32 NationIndex);

protected:
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	APlayerController* GetOwningPC() const;

	TSharedPtr<SWidget> MenuWidget;
	bool bPrevShowCursor = false;
};
