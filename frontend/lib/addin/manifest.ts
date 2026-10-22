import { createHash } from 'node:crypto';

/**
 * The Word add-in's manifest for one deployment, as `/addin/manifest.xml` serves it.
 *
 * Everything in it that differs between deployments comes from the deployment itself:
 * its own address, the Entra app it signs in with (`AUTH_MICROSOFT_ENTRA_ID_ID`) and its
 * version. So an admin publishes the add-in by pasting one URL, instead of filling in a
 * template by hand.
 */
export type ManifestSettings = {
  /** The frontend's public origin, such as `https://draftdetective.example.com`. */
  frontendUrl: string;
  /** The Entra app's client id, which Office single sign-on asks a token for. */
  clientId: string;
  /** The app's version, `major.minor.patch`. */
  version: string;
};

// Namespace for the add-in ids derived from a host (a UUID v4 picked once, never reused).
const ID_NAMESPACE = '6f1d6c2e-3b8a-4c1e-9a52-2f0d4b7e8c13';

/**
 * The add-in's id: one per frontend host, the same every time it is asked for.
 *
 * Office tells add-ins apart by id, so two deployments published in one tenant (dev and
 * production, say) must not share one, and one deployment must keep its own across
 * releases, or Office would see a new add-in each time. A UUID v5 of the host is both.
 */
export function addinId(host: string): string {
  const namespace = Buffer.from(ID_NAMESPACE.replace(/-/g, ''), 'hex');
  const hash = createHash('sha1').update(namespace).update(host.toLowerCase()).digest();
  hash[6] = (hash[6] & 0x0f) | 0x50;
  hash[8] = (hash[8] & 0x3f) | 0x80;
  const hex = hash.subarray(0, 16).toString('hex');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/** Office wants four numbers; the app has three. */
export function manifestVersion(version: string): string {
  const parts = version.split('.').map((part) => Number.parseInt(part, 10) || 0);
  return [...parts, 0, 0, 0, 0].slice(0, 4).join('.');
}

export function addinManifest({ frontendUrl, clientId, version }: ManifestSettings): string {
  const origin = new URL(frontendUrl).origin;
  const host = new URL(origin).host;
  const url = escapeXml(origin);
  const id = escapeXml(clientId);
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:bt="http://schemas.microsoft.com/office/officeappbasictypes/1.0" xmlns:ov="http://schemas.microsoft.com/office/taskpaneappversionoverrides" xsi:type="TaskPaneApp">
  <Id>${addinId(host)}</Id>
  <Version>${manifestVersion(version)}</Version>
  <ProviderName>Draft Detective</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="Draft Detective"/>
  <Description DefaultValue="Chat with Draft Detective about your document, and apply its comments and suggested changes."/>
  <IconUrl DefaultValue="${url}/logo_160x160.png"/>
  <HighResolutionIconUrl DefaultValue="${url}/logo_160x160.png"/>
  <SupportUrl DefaultValue="${url}/"/>
  <AppDomains>
    <AppDomain>${url}</AppDomain>
  </AppDomains>
  <Hosts>
    <Host Name="Document"/>
  </Hosts>
  <DefaultSettings>
    <SourceLocation DefaultValue="${url}/addin"/>
  </DefaultSettings>
  <Permissions>ReadWriteDocument</Permissions>

  <VersionOverrides xmlns="http://schemas.microsoft.com/office/taskpaneappversionoverrides" xsi:type="VersionOverridesV1_0">
    <Hosts>
      <Host xsi:type="Document">
        <Runtimes>
          <Runtime resid="Taskpane.Url" lifetime="long" />
        </Runtimes>
        <DesktopFormFactor>
          <GetStarted>
            <Title resid="GetStarted.Title"/>
            <Description resid="GetStarted.Description"/>
            <LearnMoreUrl resid="GetStarted.LearnMoreUrl"/>
          </GetStarted>
          <FunctionFile resid="Commands.Url"/>
          <ExtensionPoint xsi:type="PrimaryCommandSurface">
            <OfficeTab id="TabHome">
              <Group id="CommandsGroup">
                <Label resid="CommandsGroup.Label"/>
                <Icon>
                  <bt:Image size="16" resid="Icon.16x16"/>
                  <bt:Image size="32" resid="Icon.32x32"/>
                  <bt:Image size="80" resid="Icon.80x80"/>
                </Icon>
                <Control xsi:type="Button" id="TaskpaneButton">
                  <Label resid="TaskpaneButton.Label"/>
                  <Supertip>
                    <Title resid="TaskpaneButton.Label"/>
                    <Description resid="TaskpaneButton.Tooltip"/>
                  </Supertip>
                  <Icon>
                    <bt:Image size="16" resid="Icon.16x16"/>
                    <bt:Image size="32" resid="Icon.32x32"/>
                    <bt:Image size="80" resid="Icon.80x80"/>
                  </Icon>
                  <Action xsi:type="ShowTaskpane">
                    <TaskpaneId>ButtonId1</TaskpaneId>
                    <SourceLocation resid="Taskpane.Url"/>
                  </Action>
                </Control>
              </Group>
            </OfficeTab>
          </ExtensionPoint>
        </DesktopFormFactor>
      </Host>
    </Hosts>
    <Resources>
      <bt:Images>
        <bt:Image id="Icon.16x16" DefaultValue="${url}/logo_16x16.png"/>
        <bt:Image id="Icon.32x32" DefaultValue="${url}/logo_32x32.png"/>
        <bt:Image id="Icon.80x80" DefaultValue="${url}/logo_80x80.png"/>
      </bt:Images>
      <bt:Urls>
        <bt:Url id="GetStarted.LearnMoreUrl" DefaultValue="https://go.microsoft.com/fwlink/?LinkId=276812"/>
        <bt:Url id="Taskpane.Url" DefaultValue="${url}/addin"/>
        <!-- The manifest schema requires a function file; the add-in has no function
             commands, so it is the pane's page. -->
        <bt:Url id="Commands.Url" DefaultValue="${url}/addin"/>
      </bt:Urls>
      <bt:ShortStrings>
        <bt:String id="GetStarted.Title" DefaultValue="Get started with the Draft Detective add-in!"/>
        <bt:String id="CommandsGroup.Label" DefaultValue="Draft Detective"/>
        <bt:String id="TaskpaneButton.Label" DefaultValue="Draft Detective"/>
      </bt:ShortStrings>
      <bt:LongStrings>
        <bt:String id="GetStarted.Description" DefaultValue="The Draft Detective add-in loaded successfully. Go to the HOME tab and click the 'Draft Detective' button to get started."/>
        <bt:String id="TaskpaneButton.Tooltip" DefaultValue="Click to open the Draft Detective add-in."/>
      </bt:LongStrings>
    </Resources>
    <!-- Office single sign-on: the Entra app the pane asks Office for a token for.
         Without it the pane signs in through the dialog instead. -->
    <WebApplicationInfo>
      <Id>${id}</Id>
      <Resource>api://${escapeXml(host)}/${id}</Resource>
      <Scopes>
        <Scope>openid</Scope>
        <Scope>profile</Scope>
      </Scopes>
    </WebApplicationInfo>
  </VersionOverrides>
</OfficeApp>
`;
}

function escapeXml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
