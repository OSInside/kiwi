<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv71to72">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv71to72"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>7.1</literal> to <literal>7.2</literal>.
</para>
<xsl:template match="image" mode="conv71to72">
    <xsl:choose>
        <!-- nothing to do if already at 7.2 -->
        <xsl:when test="@schemaversion > 7.1">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.2">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv71to72"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<para xmlns="http://docbook.org/ns/docbook">
    Move bootloader, bootloader_console, boottimeout
    and zipl_targettype attributes from types into a new
    bootloader subsection
</para>
<xsl:template match="type" mode="conv71to72">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'bootloader') and not(local-name(.) = 'bootloader_console') and not(local-name(.) = 'boottimeout') and not(local-name(.) = 'zipl_targettype')]"/>
        <xsl:variable name="loadername" select="@bootloader"/>
        <xsl:variable name="loaderconsole" select="@bootloader_console"/>
        <xsl:variable name="loadertime" select="@boottimeout"/>
        <xsl:variable name="loadertarget" select="@zipl_targettype"/>
        <xsl:choose>
            <xsl:when test="@bootloader!=''">
                <bootloader>
                    <xsl:attribute name="name">
                        <xsl:value-of select="$loadername"/>
                    </xsl:attribute>
                    <xsl:choose>
                        <xsl:when test="@bootloader_console!=''">
                            <xsl:attribute name="console">
                                <xsl:value-of select="$loaderconsole"/>
                            </xsl:attribute>
                        </xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="@boottimeout!=''">
                            <xsl:attribute name="timeout">
                                <xsl:value-of select="$loadertime"/>
                            </xsl:attribute>
                        </xsl:when>
                    </xsl:choose>
                    <xsl:choose>
                        <xsl:when test="@zipl_targettype!=''">
                            <xsl:attribute name="targettype">
                                <xsl:value-of select="$loadertarget"/>
                            </xsl:attribute>
                        </xsl:when>
                    </xsl:choose>
                </bootloader>
            </xsl:when>
        </xsl:choose>
        <xsl:apply-templates mode="conv71to72"/>
    </type>
</xsl:template>

</xsl:stylesheet>
