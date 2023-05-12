import { Cog6ToothIcon } from "@heroicons/react/24/outline";
import { StringParam, useQueryParam } from "use-query-params";
import { Tabs } from "../../components/tabs";
import { QSP } from "../../config/qsp";
import TabPassword from "./tab-account";
import TabPreferences from "./tab-preferences";
import TabProfile from "./tab-profile";
import TabTokens from "./tab-tokens";

const PROFILE_TABS = {
  PREFERENCES: "Preferences",
  PROFILE: "Profile",
  TOKENS: "API Tokens",
  ACCOUNT: "Account",
};

const tabs = [
  {
    label: PROFILE_TABS.PROFILE,
    name: "profile",
  },
  {
    label: PROFILE_TABS.PREFERENCES,
    name: "preferences",
  },
  {
    label: PROFILE_TABS.TOKENS,
    name: "tokens",
  },
  {
    label: PROFILE_TABS.ACCOUNT,
    name: "account",
  },
];

const renderContent = (tab: string | null | undefined) => {
  switch (tab) {
    case PROFILE_TABS.TOKENS:
      return <TabTokens />;
    case PROFILE_TABS.ACCOUNT:
      return <TabPassword />;
    case PROFILE_TABS.PREFERENCES:
      return <TabPreferences />;
    default:
      return <TabProfile />;
  }
};

export default function UserProfile() {
  const [qspTab] = useQueryParam(QSP.TAB, StringParam);
  return (
    <div className="flex flex-col flex-1">
      <div className="border-b border-gray-200 bg-white px-4 py-5 sm:px-6">
        <div className="-ml-4 -mt-4 flex flex-wrap items-center justify-between sm:flex-nowrap">
          <div className="ml-4 mt-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <img
                  className="h-12 w-12 rounded-full"
                  src="https://ca.slack-edge.com/T04KB9WLQ5T-U04JZMS34P9-7b703e5d0a6d-512"
                  alt=""
                />
              </div>
              <div className="ml-4">
                <h3 className="text-base font-semibold leading-6 text-gray-900">Damien Garros</h3>
                <p className="text-sm text-gray-500">
                  <a href="#">@dgarros</a>
                </p>
              </div>
            </div>
          </div>
          <div className="ml-4 mt-4 flex flex-shrink-0">
            <Cog6ToothIcon className="w-6 h-6 text-gray-600 cursor-pointer hover:scale-110" />
          </div>
        </div>
      </div>
      <Tabs tabs={tabs} />
      {renderContent(qspTab)}
    </div>
  );
}
